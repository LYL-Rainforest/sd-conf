# ComfyUI Workflow

## 推送配置到 GitHub

用户说 **"push gh"** 时，执行：

```powershell
Set-Location -LiteralPath sd_conf
git add -A
git commit -m "update config"
git push
```

- 仓库：`https://github.com/LYL-Rainforest/sd-conf.git`
- 分支：`main`

## 环境配置

- ComfyUI: `E:\sd-comfyui`
- Bridge: `E:\sd-comfyui\comfyui_bridge.py`
- Python: `E:\sd-comfyui\python\python.exe`
- API: `http://127.0.0.1:8188`
- Output: `E:\sd-comfyui\ComfyUI\output`
- Model: `anything-v5-PrtRE.safetensors` (anime style)

### Startup

Check `http://127.0.0.1:8188/queue`. If down:

```powershell
Start-Process -FilePath "E:\sd-comfyui\python\python.exe" -ArgumentList "-u `"E:\sd-comfyui\ComfyUI\main.py`" --windows-standalone-build --listen 127.0.0.1 --port 8188" -NoNewWindow -RedirectStandardOutput "E:\sd-comfyui\comfyui_out.log" -RedirectStandardError "E:\sd-comfyui\comfyui_err.log"
```

## 出图流程

### 步骤1：出图筛选（默认）

```powershell
& "E:\sd-comfyui\python\python.exe" "E:\sd-comfyui\comfyui_bridge.py" --prompt "prompt here" [--steps 40] [--cfg 7] [--seed 42]
```

- 直接出 **960×540 (16:9)** 品质图，不加`--4k`
- 用户挑选满意的图，把 prompt + seed 发给我

### 步骤2：指定4K放大

```powershell
& "E:\sd-comfyui\python\python.exe" "E:\sd-comfyui\comfyui_bridge.py" --prompt "prompt here" --4k [--steps 30] [--cfg 7] [--seed 42]
```

- 加 `--4k`：960×540 → 4x AI放大 → ControlNet细节精修 → **3840×2160**
- **优化参数**：tile 896²、dpmpp_2m 采样器、Pass 1 10步 + Pass 2 8步
- 约 **1分50秒** 出图

### 迭代出图流程（风格动态偏移）

每次生成 **5张**，用户挑一张喜欢的，下次就往那张的风格方向上偏移生成。

| 轮次 | 操作 |
|------|------|
| 1 | 出5张初稿 → 用户挑一张（如 `00047`） |
| 2 | 用该图的 seed + 同 prompt 再出5张 → 用户继续挑 |
| 3+ | 每轮微调 prompt 细节（表情、背景、构图等），保持相同 seed 族系 |
| 4K | 用户最终选定后，给 seed + prompt → 加 `--4k` 放大 |

## 约定规则

### 4K 工作流说明

| 你说 | 含义 | 操作 |
|------|------|------|
| **4k** | 先出960×540筛选 → 再对选中的图4x放大+精修到4K | 我发你 prompt+seed → 你加 `--4k` 跑 |
| **原生4k** | 直接生成3840×2160 | 不加 `--4k`，手动修改bridge脚本width/height为3840×2160 |

- 如用户只说"4k"而未说"原生4k"，一律使用 `--4k` 放大流程
- **bridge脚本已优化**：tile 512→896, 采样器 dpmpp_3m_sde→dpmpp_2m, 步数 20+15→10+8

### 其他参数

- `--portrait` 竖版（540×960）
- `--jxl` 切换 Juggernaut XL 模型
- 用户说"优化细节"时，在不改变已选风格前提下微调 prompt 描述
