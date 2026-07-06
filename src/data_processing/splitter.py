from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


# 对单个标签子集执行随机切分

def split_group_indices(indices: np.ndarray, first_ratio: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    random_generator = np.random.default_rng(seed)
    shuffled_indices = indices.copy()
    random_generator.shuffle(shuffled_indices)
    split_position = int(round(len(shuffled_indices) * first_ratio))
    first_part = shuffled_indices[:split_position]
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
    train_validation_indices: list[int] = []
    test_indices: list[int] = []

    for _, group_df in df.groupby(target_column):
        group_indices = group_df.index.to_numpy()
        group_test_indices, group_train_validation_indices = split_group_indices(
            group_indices,
            test_size,
            random_seed,
        )
        test_indices.extend(group_test_indices.tolist())
        train_validation_indices.extend(group_train_validation_indices.tolist())

    train_validation_df = df.loc[sorted(train_validation_indices)].reset_index(drop=True)
    test_df = df.loc[sorted(test_indices)].reset_index(drop=True)

    train_indices: list[int] = []
    validation_indices: list[int] = []
    for _, group_df in train_validation_df.groupby(target_column):
        group_indices = group_df.index.to_numpy()
        group_validation_indices, group_train_indices = split_group_indices(
            group_indices,
            validation_size,
            random_seed + 1,
        )
        validation_indices.extend(group_validation_indices.tolist())
        train_indices.extend(group_train_indices.tolist())

    train_df = train_validation_df.loc[sorted(train_indices)].reset_index(drop=True)
    validation_df = train_validation_df.loc[sorted(validation_indices)].reset_index(drop=True)

    return {
        "train": train_df,
        "validation": validation_df,
        "test": test_df,
    }
