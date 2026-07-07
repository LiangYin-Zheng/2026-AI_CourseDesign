from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


# 对单个标签子集执行随机切分
def split_group_indices(indices: np.ndarray, first_ratio: float, seed: int) -> tuple[np.ndarray, np.ndarray]:

    # 初始化随机数生成器
    random_generator = np.random.default_rng(seed)
    # 复制索引，避免修改原数组
    shuffled_indices = indices.copy()
    # 打乱索引顺序
    random_generator.shuffle(shuffled_indices)
    # 计算切分位置
    split_position = int(round(len(shuffled_indices) * first_ratio))
    # 获取前半部分索引
    first_part = shuffled_indices[:split_position]
    # 获取后半部分索引
    second_part = shuffled_indices[split_position:]
    return first_part, second_part


# 按标签分层切分数据集
def stratified_split_dataframe(
    df: pd.DataFrame,
    target_column: str,
    test_size: float,
    validation_size: float,
    random_seed: int,
) -> Dict[str, pd.DataFrame]:

    # 保存训练集和验证集候选索引
    train_validation_indices: list[int] = []
    # 保存测试集索引
    test_indices: list[int] = []

    # 按目标标签分组后分别切分
    for _, group_df in df.groupby(target_column):
        # 获取当前组的索引
        group_indices = group_df.index.to_numpy()
        # 先切出测试集，再保留训练和验证候选集
        group_test_indices, group_train_validation_indices = split_group_indices(
            group_indices,
            test_size,
            random_seed,
        )
        # 累加测试集索引
        test_indices.extend(group_test_indices.tolist())
        # 累加训练和验证候选索引
        train_validation_indices.extend(group_train_validation_indices.tolist())

    # 生成训练和验证候选数据集
    train_validation_df = df.loc[sorted(train_validation_indices)].reset_index(drop=True)
    # 生成测试数据集
    test_df = df.loc[sorted(test_indices)].reset_index(drop=True)

    # 保存训练集索引
    train_indices: list[int] = []
    # 保存验证集索引
    validation_indices: list[int] = []
    # 再次按目标标签分组，切分训练集和验证集
    for _, group_df in train_validation_df.groupby(target_column):
        # 获取当前组的索引
        group_indices = group_df.index.to_numpy()
        # 切出验证集和训练集
        group_validation_indices, group_train_indices = split_group_indices(
            group_indices,
            validation_size,
            random_seed + 1,
        )
        # 累加验证集索引
        validation_indices.extend(group_validation_indices.tolist())
        # 累加训练集索引
        train_indices.extend(group_train_indices.tolist())

    # 生成训练集
    train_df = train_validation_df.loc[sorted(train_indices)].reset_index(drop=True)
    # 生成验证集
    validation_df = train_validation_df.loc[sorted(validation_indices)].reset_index(drop=True)

    # 返回切分结果
    return {
        "train": train_df,
        "validation": validation_df,
        "test": test_df,
    }
