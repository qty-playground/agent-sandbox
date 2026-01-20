# Agent Sandbox Testing Prompt

這是一個用於測試新 agent 在 sandbox 環境下運作的標準流程。當需要測試某個 agent 是否能在 agbox 中正常運作時，請按照以下步驟進行。

## 測試目標

驗證 agent 能否在 sandbox 環境中正常運作，並修正任何權限相關的問題。

## 測試流程

### 1. 啟動 agbox-debug 監看

在背景啟動 agbox-debug 來即時監看 sandbox violations：

```bash
agbox-debug &
```

這會建立一個背景任務，持續監看並記錄所有 sandbox 違規事件。

### 2. 執行 agent 測試

使用 agbox 啟動要測試的 agent，並給予簡單的測試指令：

```bash
agbox <agent-command> -p "簡單的測試指令"
```

範例：
- `agbox c4d -p "hello, 請回應一句話即可"`
- `agbox gemini -y -p "讀取當前目錄的 README.md 前 10 行"`
- `agbox codex -p "執行 python --version"`

### 3. 檢查測試結果

觀察兩個方面：

1. **Agent 輸出**：agent 是否成功啟動並正常回應
2. **錯誤訊息**：是否出現權限相關的錯誤

常見的權限錯誤訊息格式：
- `Error: EPERM: operation not permitted, open '...'`
- `PermissionError: [Errno 1] Operation not permitted: '...'`

### 4. 分析 agbox-debug 輸出

如果發現權限錯誤，檢查 agbox-debug 的輸出：

```bash
# 查看最近的違規記錄
tail -100 <agbox-debug-output-file> | grep -E "(deny|agent-name)"

# 或即時查看最新輸出
tail -f <agbox-debug-output-file>
```

重點關注：
- `deny(1) file-read-*` - 讀取被阻擋
- `deny(1) file-write-*` - 寫入被阻擋
- 被阻擋的檔案路徑

### 5. 修正權限問題

根據 agbox-debug 輸出的違規記錄，在 `src/agent_sandbox/cli.py` 中加入對應的權限。

#### 5.1 確定權限類型

判斷需要的權限：
- **僅讀取**：設定檔、配置目錄（唯讀）
- **讀寫**：log 檔、cache、狀態檔

#### 5.2 選擇適當的區塊

在 `get_agent_rules()` 函數中加入 agent 專屬權限：

```python
def get_agent_rules(agent: str, home: Path) -> str:
    """
    Common agent configuration rules
    """
    return f"""
;; Allow <Agent Name> config (read and write)
(allow file-read* file-write*
    (subpath "{{home}}/.agent-config-dir"))
"""
```

常見的權限模式：

**A. Agent 配置目錄（讀寫）**
```scheme
;; Allow <Agent> config (read and write)
(allow file-read* file-write*
    (subpath "{home}/.agent-dir"))
```

**B. 特定配置檔（讀寫）**
```scheme
(allow file-read* file-write*
    (literal "{home}/.agent-config.json")
    (literal "{home}/.agent-config.lock"))
```

**C. 開發工具目錄（唯讀）**
在 `generate_sandbox_profile()` 的開發工具區塊：
```scheme
;; ALLOWED: Development tool directories (read-only)
(allow file-read*
    (literal "{home}/.tool-config"))
```

**D. Cache/Metadata（讀寫）**
在 cache 區塊：
```scheme
;; ALLOWED: Cache and config directories (read-write)
(allow file-read* file-write*
    (subpath "{home}/.tool/metadata"))
```

#### 5.3 套用修正的路徑模式

| 路徑類型 | 使用指令 | 範例 |
|---------|---------|------|
| 單一檔案 | `(literal "path")` | `.condarc`, `.claude.json.lock` |
| 整個目錄 | `(subpath "path")` | `.claude/`, `.gemini/` |
| 模式比對 | `(regex #"pattern")` | `\\.zcompdump.*$` |

### 6. 重新測試

修正後，重新執行步驟 2 的測試指令，確認：
1. Agent 能正常運作
2. agbox-debug 不再顯示相關的違規記錄

### 7. 提交修改

確認測試通過後，建立 commit：

```bash
git add src/agent_sandbox/cli.py
git commit -m "Add <agent-name> permissions

- Add <file/directory> read/write access
- Fixes: <描述解決的問題>
"
git push
```

## 常見問題排查

### Q1: Agent 啟動但有警告訊息

檢查警告訊息中提到的檔案路徑，可能是非關鍵的配置檔被阻擋。評估是否需要加入權限。

### Q2: 找不到 agbox-debug 輸出檔案

agbox-debug 以背景任務運行時，輸出會寫入 `/var/folders/.../tasks/<task-id>.output`。使用 `jobs` 或檢查背景任務訊息找到檔案路徑。

### Q3: 不確定該用 literal 還是 subpath

- 單一檔案 → `literal`
- 整個目錄及其內容 → `subpath`
- 有規律的檔名模式 → `regex`

## 測試範例

### 範例 1: 測試 Claude Code (c4d)

```bash
# 1. 啟動監看
agbox-debug &

# 2. 測試
agbox c4d -p "hello"

# 3. 發現錯誤：無法寫入 .claude.json.lock
# 4. 檢查 agbox-debug：
#    Sandbox: node deny(1) file-write-create /Users/xxx/.claude.json.lock

# 5. 修正：在 get_agent_rules() 加入
(allow file-read* file-write*
    (literal "{home}/.claude.json.lock"))

# 6. 重新測試 → 成功
```

### 範例 2: 測試 Gemini CLI

```bash
# 1. 啟動監看
agbox-debug &

# 2. 測試
agbox gemini -y -p "hello"

# 3. 發現錯誤：EPERM: operation not permitted, open '.gemini/settings.json'

# 4. 修正：在 get_agent_rules() 加入
(allow file-read* file-write*
    (subpath "{home}/.gemini"))

# 5. 重新測試 → 成功
```

## 注意事項

1. **最小權限原則**：只開放必要的權限，優先使用 `literal` 而非 `subpath`
2. **區分讀寫**：設定檔通常只需 read，log/cache 才需要 write
3. **測試徹底**：不只測試啟動，也要測試 agent 的主要功能（讀檔、寫檔、執行指令等）
4. **記錄違規**：保留 agbox-debug 輸出作為參考
5. **版本控制**：每個修正都應該獨立 commit，便於追蹤和回溯
