// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
export const getHeaderCounterText = (items = [], selectedItems = []) => {
  return selectedItems && selectedItems.length > 0
    ? `(${selectedItems.length}/${items.length})`
    : `(${items.length})`;
};

export const getServerHeaderCounterText = (totalCount, selectedItems) => {
  return selectedItems && selectedItems.length > 0
    ? `(${selectedItems.length}/${totalCount}+)`
    : `(${totalCount}+)`;
};

export const getServerFilterCounterText = (
  items = [],
  pagesCount,
  pageSize
) => {
  const count =
    pagesCount > 1 ? `${pageSize * (pagesCount - 1)}+` : items.length + "";
  return `${count} 条匹配`;
};

export const getFilterCounterText = (count) => `${count} 条匹配`;
