from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from src.analysis.analyzer import build_analysis_summary, render_analysis_markdown
from src.config import load_project_config
from src.data_processing.cleaner import clean_dataset
from src.data_processing.loader import load_dataset
from src.data_processing.splitter import stratified_split_dataframe
from src.evaluation.reporter import render_family_comparison_report, save_model_report
from src.features.preprocessor import TabularPreprocessor
from src.interfaces.desktop.app import run_local_gui
from src.interfaces.web.server import run_server
from src.models.manual_trainer import count_manual_training_units, train_all_models
from src.models.sklearn_trainer import count_sklearn_training_units, train_sklearn_models
from src.serving.inference import load_inference_bundle, predict_single
from src.utils.file_utils import ensure_directory, write_json, write_text
from src.utils.logger import configure_project_logging, format_kv_pairs, get_logger
from src.utils.progress import WorkflowProgress
from src.visualization.svg_plotter import save_bar_chart, save_heatmap, save_histogram
from src.visualization.training_plots import save_named_metric_bars

logger = get_logger('main')


def initialize_output_directories(config: Dict[str, Any]) -> None:
    for output_path in config['output_dirs'].values():
        ensure_directory(output_path)
    for extra_directory in [
        Path(config['output_dirs']['figures']) / 'eda',
        Path(config['output_dirs']['figures']) / 'training',
        Path(config['output_dirs']['figures']) / 'comparison',
        Path(config['output_dirs']['models']) / 'sklearn',
        Path(config['output_dirs']['models']) / 'manual',
        Path(config['output_dirs']['logs']),
    ]:
        ensure_directory(extra_directory)


def build_training_progress(config: Dict[str, Any], command: str) -> WorkflowProgress:
    total_units = 4  # 数据准备 3 步 + 最终汇总 1 步
    if command in {'train', 'train-sklearn'}:
        total_units += count_sklearn_training_units(config)
    if command in {'train', 'train-manual'}:
        total_units += count_manual_training_units(config)
    return WorkflowProgress(total_units=total_units, logger_name='training-progress')


def generate_eda_visualizations(clean_df, analysis_summary: Dict[str, Any], config: Dict[str, Any]) -> None:
    figure_dir = Path(config['output_dirs']['figures']) / 'eda'
    target_distribution = analysis_summary['target_distribution']
    save_bar_chart(list(target_distribution.keys()), [float(value) for value in target_distribution.values()], '肥胖等级类别分布图', figure_dir / 'class_distribution.svg')
    for feature_name, title in [('age', '年龄分布图'), ('height_m', '身高分布图'), ('weight_kg', '体重分布图'), ('bmi', 'BMI 分布图')]:
        save_histogram(clean_df[feature_name].to_numpy(), int(config['visualization']['histogram_bins']), title, figure_dir / f'{feature_name}_histogram.svg')
    numeric_features = config['analysis_numeric_features']
    correlation_matrix = clean_df[numeric_features].corr().to_numpy(dtype=float)
    save_heatmap(correlation_matrix, numeric_features, numeric_features, '核心数值特征相关性热力图', figure_dir / 'correlation_heatmap.svg')


def prepare_training_context(config: Dict[str, Any], progress: WorkflowProgress) -> Dict[str, Any]:
    raw_df = load_dataset(config['data_path'])
    clean_df = clean_dataset(raw_df, config)
    clean_df.to_csv(Path(config['output_dirs']['analysis']) / 'clean_dataset.csv', index=False, encoding='utf-8-sig')
    progress.advance('读取与清洗数据', f'raw_rows={len(raw_df)} | clean_rows={len(clean_df)}')

    analysis_summary = build_analysis_summary(clean_df, config)
    write_json(Path(config['output_dirs']['analysis']) / 'eda_summary.json', analysis_summary)
    write_text(Path(config['output_dirs']['reports']) / 'eda_summary.md', render_analysis_markdown(analysis_summary))
    generate_eda_visualizations(clean_df, analysis_summary, config)
    progress.advance('EDA 与图表生成', f"class_count={clean_df[config['target_column']].nunique()}")

    datasets = stratified_split_dataframe(clean_df, config['target_column'], float(config['test_size']), float(config['validation_size']), int(config['random_seed']))
    progress.advance('数据集切分', f"train={len(datasets['train'])} | validation={len(datasets['validation'])} | test={len(datasets['test'])}")
    return {'raw_df': raw_df, 'clean_df': clean_df, 'analysis_summary': analysis_summary, 'datasets': datasets}


def build_preprocessor(config: Dict[str, Any], datasets: Dict[str, Any]) -> TabularPreprocessor:
    preprocessor = TabularPreprocessor(numeric_features=config['numeric_features'], categorical_features=config['categorical_features'])
    preprocessor.fit(datasets['train'], config['target_column'])
    return preprocessor


def run_sklearn_training_pipeline(config: Dict[str, Any], context: Dict[str, Any], progress: WorkflowProgress) -> Dict[str, Any]:
    logger.info('sklearn 训练链路启动。')
    training_summary = train_sklearn_models(context['datasets'], config, progress_callback=progress.advance)
    save_model_report(Path(config['output_dirs']['reports']) / 'sklearn_family_report.md', training_summary['model_results'], family_name='sklearn 模型')
    return training_summary


def run_manual_training_pipeline(config: Dict[str, Any], context: Dict[str, Any], progress: WorkflowProgress) -> Dict[str, Any]:
    logger.info('手搓训练链路启动。')
    preprocessor = build_preprocessor(config, context['datasets'])
    training_summary = train_all_models(context['datasets'], preprocessor, config, progress_callback=progress.advance)
    save_model_report(Path(config['output_dirs']['reports']) / 'manual_family_report.md', training_summary['model_results'], family_name='手搓模型')
    return training_summary


def _collect_artifacts(config: Dict[str, Any]) -> Dict[str, list[str]]:
    artifact_map: Dict[str, list[str]] = {}
    for name, directory in config['output_dirs'].items():
        base_path = Path(directory)
        if not base_path.exists():
            artifact_map[name] = []
            continue
        artifact_map[name] = sorted(str(path.resolve().relative_to(Path(config['project_root']).resolve())) for path in base_path.rglob('*') if path.is_file())
    return artifact_map


def build_dashboard_summary(config: Dict[str, Any], context: Dict[str, Any], sklearn_summary: Dict[str, Any] | None, manual_summary: Dict[str, Any] | None) -> Dict[str, Any]:
    comparison_rows: list[dict[str, Any]] = []
    parameter_tables: list[dict[str, Any]] = []

    if sklearn_summary is not None:
        for model_name, result in sklearn_summary['model_results']['optimized'].items():
            comparison_rows.append({'family': 'sklearn', 'name': model_name, 'metrics': result['test_metrics']})
            parameter_tables.append({'family': 'sklearn', 'name': model_name, 'parameters': result['parameters']})
    if manual_summary is not None:
        for model_name, result in manual_summary['model_results']['optimized'].items():
            comparison_rows.append({'family': 'manual', 'name': model_name, 'metrics': result['test_metrics']})
            parameter_tables.append({'family': 'manual', 'name': model_name, 'parameters': result['parameters']})

    recommended = {'family': 'unknown', 'name': 'unknown', 'macro_f1': -1.0}
    for row in comparison_rows:
        macro_f1 = float(row['metrics']['macro_f1'])
        if macro_f1 > float(recommended['macro_f1']):
            recommended = {'family': row['family'], 'name': row['name'], 'macro_f1': macro_f1}

    if comparison_rows:
        save_named_metric_bars(
            [{'name': f"{row['family']}/{row['name']}", 'metrics': row['metrics']} for row in comparison_rows],
            Path(config['output_dirs']['figures']) / 'comparison' / 'full_model_metric_comparison.png',
            'sklearn 与手搓模型总体指标对比图',
        )

    return {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'project_name': config['project_name'],
        'dataset': {
            'sample_count': len(context['clean_df']),
            'class_count': context['clean_df'][config['target_column']].nunique(),
            'target_column': config['target_column'],
            'split': {'train': len(context['datasets']['train']), 'validation': len(context['datasets']['validation']), 'test': len(context['datasets']['test'])},
        },
        'analysis_summary': context['analysis_summary'],
        'families': {'sklearn': sklearn_summary, 'manual': manual_summary},
        'comparison_rows': comparison_rows,
        'parameter_tables': parameter_tables,
        'recommended_model': recommended,
        'artifacts': _collect_artifacts(config),
    }


def log_parameter_summary(parameter_tables: list[dict[str, Any]]) -> None:
    if not parameter_tables:
        return
    logger.info('优化后参数汇总：')
    for row in parameter_tables:
        logger.info('  %s/%s -> %s', row['family'], row['name'], format_kv_pairs(row['parameters']))


def finalize_training_outputs(
    config: Dict[str, Any],
    context: Dict[str, Any],
    sklearn_summary: Dict[str, Any] | None,
    manual_summary: Dict[str, Any] | None,
    progress: WorkflowProgress,
) -> Dict[str, Any]:
    dashboard_summary = build_dashboard_summary(config, context, sklearn_summary, manual_summary)
    write_json(Path(config['output_dirs']['evaluation']) / 'training_dashboard.json', dashboard_summary)
    write_text(Path(config['output_dirs']['reports']) / 'family_comparison_report.md', render_family_comparison_report(dashboard_summary))
    final_report_lines = [
        '# 项目训练交付摘要',
        '',
        f"- 数据集规模：{dashboard_summary['dataset']['sample_count']} 条样本",
        f"- 标签类别数：{dashboard_summary['dataset']['class_count']} 类",
        f"- 推荐部署模型：{dashboard_summary['recommended_model']['family']} / {dashboard_summary['recommended_model']['name']}",
        f"- 推荐模型 Macro F1：{dashboard_summary['recommended_model']['macro_f1']}",
        f"- 仪表盘摘要：{Path(config['output_dirs']['evaluation']) / 'training_dashboard.json'}",
        f"- 日志文件：{Path(config['output_dirs']['logs']) / 'project.log'}",
    ]
    write_text(Path(config['output_dirs']['reports']) / 'final_summary.md', '\n'.join(final_report_lines))
    progress.advance('汇总交付结果', f"recommended={dashboard_summary['recommended_model']['family']}/{dashboard_summary['recommended_model']['name']}")
    log_parameter_summary(dashboard_summary['parameter_tables'])
    logger.info('交付摘要完成：recommended=%s/%s | macro_f1=%s', dashboard_summary['recommended_model']['family'], dashboard_summary['recommended_model']['name'], dashboard_summary['recommended_model']['macro_f1'])
    return dashboard_summary


def run_prediction_command(json_text: str | None, payload_file: str | None) -> None:
    if not json_text and not payload_file:
        raise ValueError('predict 命令必须提供 --json 或 --payload-file。')
    if payload_file:
        payload = json.loads(Path(payload_file).read_text(encoding='utf-8'))
    else:
        payload = json.loads(json_text or '{}')
    config = load_project_config()
    bundle = load_inference_bundle(config)
    result = predict_single(payload, config, bundle)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='肥胖风险预测系统主入口')
    subparsers = parser.add_subparsers(dest='command', required=True)
    subparsers.add_parser('train', help='执行完整训练主链路：EDA + sklearn + 手搓 + 对比摘要')
    subparsers.add_parser('train-sklearn', help='仅执行 sklearn 版本数据处理、训练、评估与图表生成')
    subparsers.add_parser('train-manual', help='仅执行手搓版本训练流程，作为对照实验')

    serve_web_parser = subparsers.add_parser('serve-web', help='启动本地 HTTPS Web 演示服务')
    serve_web_parser.add_argument('--host', default='127.0.0.1')
    serve_web_parser.add_argument('--port', type=int, default=8000)
    serve_web_parser.add_argument('--certfile', default=None, help='HTTPS 证书文件路径，默认自动生成临时自签证书')
    serve_web_parser.add_argument('--keyfile', default=None, help='HTTPS 私钥文件路径，默认自动生成临时自签私钥')

    serve_alias_parser = subparsers.add_parser('serve', help='serve-web 的兼容别名')
    serve_alias_parser.add_argument('--host', default='127.0.0.1')
    serve_alias_parser.add_argument('--port', type=int, default=8000)
    serve_alias_parser.add_argument('--certfile', default=None, help='HTTPS 证书文件路径，默认自动生成临时自签证书')
    serve_alias_parser.add_argument('--keyfile', default=None, help='HTTPS 私钥文件路径，默认自动生成临时自签私钥')

    subparsers.add_parser('gui-local', help='启动无需 HTTP 的本地桌面界面')

    predict_parser = subparsers.add_parser('predict', help='执行单条样本推理')
    predict_parser.add_argument('--json', dest='json_text', default=None)
    predict_parser.add_argument('--payload-file', dest='payload_file', default=None)
    return parser


def main() -> None:
    config = load_project_config()
    initialize_output_directories(config)
    log_path = configure_project_logging(config['project_root'], relative_log_path=config['output_dirs']['logs'] + '/project.log')
    logger.info('项目启动：%s', format_kv_pairs({'project': config['project_name'], 'seed': config['random_seed'], 'data_path': config['data_path'], 'log_file': log_path}))

    parser = build_argument_parser()
    arguments = parser.parse_args()

    if arguments.command in {'train', 'train-sklearn', 'train-manual'}:
        progress = build_training_progress(config, arguments.command)
        context = prepare_training_context(config, progress)
        sklearn_summary = None
        manual_summary = None
        if arguments.command in {'train', 'train-sklearn'}:
            sklearn_summary = run_sklearn_training_pipeline(config, context, progress)
        if arguments.command in {'train', 'train-manual'}:
            manual_summary = run_manual_training_pipeline(config, context, progress)
        finalize_training_outputs(config, context, sklearn_summary, manual_summary, progress)
    elif arguments.command in {'serve-web', 'serve'}:
        run_server(arguments.host, arguments.port, arguments.certfile, arguments.keyfile)
    elif arguments.command == 'gui-local':
        run_local_gui()
    elif arguments.command == 'predict':
        run_prediction_command(arguments.json_text, arguments.payload_file)


if __name__ == '__main__':
    main()
