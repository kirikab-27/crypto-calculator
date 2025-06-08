# React Hooks 依存配列問題解決ガイド

## 概要

このドキュメントは、React Hooks（特に `useMemo` と `useEffect`）の依存配列に関する問題と、その解決方法について記載したものです。日付フィルタリング機能の実装で数日間解決できなかった問題を基に、同様の問題を未然に防ぐためのガイドラインを提供します。

## 問題の背景

### 発生した問題

日付フィルタリング機能において、以下の症状が発生しました：
- フィルターの値を変更しても、実際のフィルタリングが正しく動作しない
- デバウンス処理が期待通りに機能しない
- state の値が最新の状態を反映しない

### 根本原因

JavaScript の**クロージャ（closure）**と React Hooks の**依存配列**の相互作用による問題でした。

## 具体的な問題コード

### 問題のあったコード

```typescript
// frontend/app/dashboard/page.tsx
const debouncedLoadTransactions = useMemo(
  () => debounce(async () => {
    if (dateValidationError) {
      return;
    }
    
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      // ここで参照される state は作成時点の値で固定される
      if (startDateFilter) params.append('start_date', startDateFilter);
      if (endDateFilter) params.append('end_date', endDateFilter);
      if (typeFilter) params.append('type', typeFilter);
      if (currencyFilter) params.append('currency', currencyFilter);
      
      // ... 以下省略
    } catch (error) {
      // エラー処理
    }
  }, 500),
  [dateValidationError, startDateFilter, endDateFilter, typeFilter, currencyFilter, currentPage, itemsPerPage]
);

// useEffect で関数を呼び出し
useEffect(() => {
  debouncedLoadTransactions();
  return () => {
    debouncedLoadTransactions.cancel();
  };
}, [currentPage, itemsPerPage, typeFilter, currencyFilter, startDateFilter, endDateFilter, forceReload, debouncedLoadTransactions]);
```

### 問題点の詳細

1. **クロージャの罠**
   - `useMemo` で作成された関数は、作成時点の state 値を「キャプチャ」する
   - debounce により 500ms 後に実行される時点では、state が既に変更されている可能性がある
   - しかし、関数内では古い値を参照してしまう

2. **依存配列の循環参照**
   - `debouncedLoadTransactions` 自体が `useEffect` の依存配列に含まれている
   - state が更新されるたびに新しい関数インスタンスが作成される
   - それがまた `useEffect` を発火させ、無限ループのリスクがある

3. **デバウンス関数の再作成**
   - 依存する値が変わるたびに新しいデバウンス関数が作成される
   - 前のデバウンスがキャンセルされ、デバウンスが正しく機能しない

## 解決方法

### 方法1: useCallback と引数を使用

```typescript
// デバウンス関数を一度だけ作成
const debouncedLoadTransactions = useCallback(
  debounce((filters: {
    startDate?: string;
    endDate?: string;
    type?: string;
    currency?: string;
    page: number;
    itemsPerPage: number;
  }) => {
    // filters パラメータとして最新の値を受け取る
    loadTransactions(filters);
  }, 500),
  [] // 依存配列は空で良い
);

// 使用時に最新の state を渡す
useEffect(() => {
  debouncedLoadTransactions({
    startDate: startDateFilter,
    endDate: endDateFilter,
    type: typeFilter,
    currency: currencyFilter,
    page: currentPage,
    itemsPerPage: itemsPerPage
  });
}, [startDateFilter, endDateFilter, typeFilter, currencyFilter, currentPage, itemsPerPage]);
```

### 方法2: useRef を使用した実装

```typescript
// 最新の値を保持する ref
const filtersRef = useRef({
  startDate: startDateFilter,
  endDate: endDateFilter,
  type: typeFilter,
  currency: currencyFilter,
  page: currentPage,
  itemsPerPage: itemsPerPage
});

// ref を更新
useEffect(() => {
  filtersRef.current = {
    startDate: startDateFilter,
    endDate: endDateFilter,
    type: typeFilter,
    currency: currencyFilter,
    page: currentPage,
    itemsPerPage: itemsPerPage
  };
}, [startDateFilter, endDateFilter, typeFilter, currencyFilter, currentPage, itemsPerPage]);

// デバウンス関数は一度だけ作成
const debouncedLoadTransactions = useMemo(
  () => debounce(() => {
    // filtersRef.current で最新の値を参照
    loadTransactions(filtersRef.current);
  }, 500),
  []
);
```

### 方法3: カスタムフックの作成

```typescript
// カスタムフック
function useDebouncedCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  deps: React.DependencyList = []
): T {
  const callbackRef = useRef(callback);
  
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback, ...deps]);
  
  const debouncedCallback = useMemo(
    () => debounce((...args: Parameters<T>) => {
      callbackRef.current(...args);
    }, delay),
    [delay]
  );
  
  return debouncedCallback as T;
}

// 使用例
const debouncedLoadTransactions = useDebouncedCallback(
  () => {
    loadTransactions({
      startDate: startDateFilter,
      endDate: endDateFilter,
      // ...
    });
  },
  500,
  [startDateFilter, endDateFilter, typeFilter, currencyFilter, currentPage, itemsPerPage]
);
```

## ベストプラクティス

### 1. 依存配列の管理

```typescript
// ❌ 悪い例：依存配列が不完全
useEffect(() => {
  console.log(value1, value2);
}, [value1]); // value2 が抜けている

// ✅ 良い例：ESLint の exhaustive-deps ルールを使用
useEffect(() => {
  console.log(value1, value2);
}, [value1, value2]);
```

### 2. 関数の依存関係

```typescript
// ❌ 悪い例：関数内で state を直接参照
const handleClick = useCallback(() => {
  doSomething(stateValue); // stateValue が古い可能性
}, []); // 依存配列が空

// ✅ 良い例：依存配列に含める or 引数として渡す
const handleClick = useCallback((value) => {
  doSomething(value);
}, []);

// 使用時
<button onClick={() => handleClick(stateValue)}>Click</button>
```

### 3. デバウンス・スロットルの実装

```typescript
// ✅ 推奨パターン
import { useMemo, useRef, useEffect } from 'react';
import debounce from 'lodash/debounce';

function useDebounce<T extends (...args: any[]) => any>(
  fn: T,
  delay: number
): T {
  const fnRef = useRef(fn);
  
  // 関数の参照を更新
  useEffect(() => {
    fnRef.current = fn;
  }, [fn]);
  
  // デバウンス関数は一度だけ作成
  const debouncedFn = useMemo(
    () => debounce((...args: Parameters<T>) => {
      fnRef.current(...args);
    }, delay),
    [delay]
  );
  
  return debouncedFn as T;
}
```

## デバッグのヒント

### 1. React DevTools の活用

- Components タブで props と state の変化を監視
- Profiler タブで再レンダリングの原因を特定

### 2. console.log での確認

```typescript
useEffect(() => {
  console.log('Effect triggered with:', { value1, value2 });
  return () => {
    console.log('Cleanup with:', { value1, value2 });
  };
}, [value1, value2]);
```

### 3. ESLint ルールの設定

```json
// .eslintrc.json
{
  "rules": {
    "react-hooks/exhaustive-deps": "warn"
  }
}
```

## チェックリスト

デバウンス処理を実装する際は、以下の点を確認してください：

- [ ] 依存配列に必要な値がすべて含まれているか
- [ ] クロージャによる古い値の参照が発生していないか
- [ ] デバウンス関数が意図せず再作成されていないか
- [ ] useCallback/useMemo の使い分けが適切か
- [ ] ESLint の exhaustive-deps ルールが有効になっているか

## まとめ

React Hooks の依存配列問題は、JavaScript のクロージャと React の再レンダリングメカニズムが複雑に絡み合うことで発生します。この問題を回避するには：

1. **依存配列を正確に管理する**
2. **クロージャの性質を理解する**
3. **適切なパターンを選択する**（引数渡し、useRef、カスタムフック）
4. **開発ツールを活用する**（ESLint、React DevTools）

これらの知識を活用することで、より堅牢な React アプリケーションを構築できます。