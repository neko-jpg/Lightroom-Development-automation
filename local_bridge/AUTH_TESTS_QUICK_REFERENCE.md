# API認証テスト - クイックリファレンス

## テストファイル

- **test_auth.py** - 認証マネージャーの単体テスト (28テスト)
- **test_auth_api.py** - 認証APIエンドポイントの統合テスト (25テスト)

## クイックスタート

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. テストの実行

```bash
# 全テストを実行
pytest local_bridge/test_auth*.py -v

# 単体テストのみ
pytest local_bridge/test_auth.py -v

# 統合テストのみ
pytest local_bridge/test_auth_api.py -v

# 特定のテストクラスを実行
pytest local_bridge/test_auth.py::TestAuthManager -v

# 特定のテストメソッドを実行
pytest local_bridge/test_auth.py::TestAuthManager::test_jwt_token_generation -v
```

### 3. カバレッジレポート

```bash
# HTMLレポートを生成
pytest local_bridge/test_auth*.py --cov=auth_manager --cov=api_auth --cov-report=html

# ターミナルにレポート表示
pytest local_bridge/test_auth*.py --cov=auth_manager --cov=api_auth --cov-report=term
```

## テストカテゴリ

### JWT認証テスト
```bash
# JWT関連のテストのみ実行
pytest local_bridge/test_auth.py -k "jwt" -v
```

### APIキー管理テスト
```bash
# APIキー関連のテストのみ実行
pytest local_bridge/test_auth.py -k "api_key" -v
```

### レート制限テスト
```bash
# レート制限関連のテストのみ実行
pytest local_bridge/test_auth.py -k "rate_limit" -v
```

### 失敗ケーステスト
```bash
# 失敗ケースのテストのみ実行
pytest local_bridge/test_auth.py::TestAuthenticationFailureCases -v
```

## 検証スクリプト

### テストモジュールの検証
```bash
python local_bridge/verify_auth_tests.py
```

このスクリプトは以下を確認します:
- テストモジュールのインポート可能性
- 必要な依存関係の存在
- テストクラスの存在

### テストの実行
```bash
python local_bridge/run_auth_tests.py
```

このスクリプトは両方のテストファイルを実行し、結果をレポートします。

## トラブルシューティング

### pytest が見つからない
```bash
pip install pytest pytest-flask
```

### インポートエラー
```bash
# Pythonパスを確認
export PYTHONPATH="${PYTHONPATH}:$(pwd)/local_bridge"

# または、local_bridgeディレクトリから実行
cd local_bridge
pytest test_auth.py -v
```

### 依存関係の問題
```bash
# 全依存関係を再インストール
pip install -r requirements.txt --force-reinstall
```

## テスト結果の例

```
test_auth.py::TestAuthManager::test_jwt_token_generation PASSED
test_auth.py::TestAuthManager::test_jwt_token_verification_valid PASSED
test_auth.py::TestAuthManager::test_api_key_generation PASSED
test_auth.py::TestAuthenticationFailureCases::test_jwt_token_tampering PASSED
...

======================== 53 passed in 2.34s ========================
```

## CI/CD統合

### GitHub Actions
```yaml
- name: Run authentication tests
  run: |
    pip install -r local_bridge/requirements.txt
    pytest local_bridge/test_auth*.py -v --cov=auth_manager --cov=api_auth
```

### GitLab CI
```yaml
test:auth:
  script:
    - pip install -r local_bridge/requirements.txt
    - pytest local_bridge/test_auth*.py -v
```

## 継続的な改善

### 新しいテストの追加

1. `test_auth.py`に単体テストを追加
2. `test_auth_api.py`に統合テストを追加
3. テストを実行して確認
4. カバレッジレポートを確認

### テストのベストプラクティス

- ✅ 各テストは独立して実行可能
- ✅ テストデータは一時ファイルを使用
- ✅ setup/teardownで環境をクリーンアップ
- ✅ 明確なテスト名とドキュメント
- ✅ エッジケースと失敗ケースをカバー

---

**最終更新**: 2025-11-09  
**テスト数**: 53個 (単体: 28, 統合: 25)  
**カバレッジ**: JWT認証、APIキー管理、レート制限、セキュリティ
