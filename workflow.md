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
Start-Process -FilePath "E:\sd-comfyui\python\python.exe" -ArgumentList "-u `"E:\sd-comfyui\ComfyUI\main.py`" --listen 127.0.0.1 --port 8188 --disable-pinned-memory --lowvram" -NoNewWindow -RedirectStandardOutput "E:\sd-comfyui\comfyui_out.log" -RedirectStandardError "E:\sd-comfyui\comfyui_err.log"
```

## 出图流程

### 步骤1：出图筛选（默认）

```powershell
& "E:\sd-comfyui\python\python.exe" "E:\sd-comfyui\comfyui_bridge.py" --prompt "prompt here" [--steps 40] [--cfg 7] [--seed 42]
```

- 直接出 **960×544 (16:9)** 品质图，不加`--4k`
- 用户挑选满意的图，把 prompt + seed 发给我

### 步骤2：指定4K放大

```powershell
& "E:\sd-comfyui\python\python.exe" "E:\sd-comfyui\comfyui_bridge.py" --prompt "prompt here" --4k [--steps 30] [--cfg 7] [--seed 42]
```

- 加 `--4k`：960×544 → 4x AI放大 → ControlNet细节精修 → **3840×2176**
- **优化参数**：tile 896²、dpmpp_2m 采样器、Pass 1 10步 + Pass 2 8步
- 约 **1分50秒** 出图

### 迭代出图流程（风格动态偏移）

用户挑一张喜欢的，下次就往那张的风格方向上偏移生成。

#### 生成量
- 每批 **10 张**，用户说画几批就几批
- 默认：1批（10张）；说"两张"=2批（20张）；"三张"=3批（30张）
- 分批策略：自动按 **5张/轮** 分轮生成，避免爆显存

| 轮次 | 操作 |
|------|------|
| 1 | 按指定量出初稿 → 用户挑一张（如 `00047`） |
| 2 | 用该图的 seed + 同 prompt 再出指定量 → 用户继续挑 |
| 3+ | 每轮微调 prompt 细节（表情、背景、构图等），保持相同 seed 族系 |
| 4K | 用户最终选定后，给 seed + prompt → 加 `--4k` 放大 |

## 约定规则

### 4K 工作流说明

| 你说 | 含义 | 操作 |
|------|------|------|
| **4k** | 先出960×544筛选 → 再对选中的图4x放大+精修到4K | 我发你 prompt+seed → 你加 `--4k` 跑 |
| **原生4k** | 直接生成3840×2160 | 不加 `--4k`，手动修改bridge脚本width/height为3840×2160 |

- 如用户只说"4k"而未说"原生4k"，一律使用 `--4k` 放大流程
- **bridge脚本已优化**：tile 512→896, 采样器 dpmpp_3m_sde→dpmpp_2m, 步数 20+15→10+8

### 已有4K放大（`--upscale`）

对已出图的图片进行4K放大+精修（3840×2160）：

```powershell
& "E:\sd-comfyui\python\python.exe" "E:\sd-comfyui\comfyui_bridge.py" --prompt "原prompt" --negative "原negative" --steps 40 --cfg 7 --batch-size 1 --upscale "E:\sd-comfyui\ComfyUI\output\图片名.png" --seed <自定义seed>
```

- 需安装模型：`control_v11f1e_sd15_tile.pth`（ControlNet）、`4x_NMKD-Superscale-SP_178000_G.pth`（放大）
- 逐张执行，避免爆显存

### 出图反馈规则

| 用户反馈 | 行为 |
|----------|------|
| "不错"、"多来" | 同 seed 继续生成 |
| "不好"、没表态 | 停止，不再生成该方向 |

### 分辨率

- 默认：**960×544**（横版）/ **544×960**（竖版 `--portrait`）
- 4K放大：对应 3840×2160 / 2160×3840

### LORA 列表（启动时分析）

每次启动 SD 后，先运行以下命令查看可用 LORA 及其底模类型：

```powershell
& "E:\sd-comfyui\python\python.exe" -c "import json,struct,os; from safetensors import safe_open
d=r'E:\sd-comfyui\ComfyUI\models\loras'
print('\n--- LORA 列表 ---')
for f in sorted(os.listdir(d)):
 if not f.endswith('.safetensors'):continue
 p=os.path.join(d,f)
 with safe_open(p,framework='pt')as h:
  k=list(h.keys());up=[x for x in k if 'lora_up' in x]
  t='SDXL' if up and h.get_tensor(up[0]).shape[0]>=2048 else 'SD1.5'
  print(f'{f:45s} {os.path.getsize(p)/1e6:5.1f}MB  {t}')
print('---\n')"
```

| LORA | 大小 | 底模 |
|------|------|------|
| `Genshin_Nahida_AP_v1.safetensors` | 37.9MB | SDXL |
| `genshin-char-model.safetensors` | 151.1MB | SDXL |
| `shenhe_pony.safetensors` | 29.0MB | SDXL (Pony) |
| `yoimiya_genshin.safetensors` | 75.6MB | SDXL |

> 所有 LORA 均为 SDXL 底模，需配合 `--jxl` 使用。Pony 类 LORA 也兼容 Juggernaut XL。

### 其他参数

- `--portrait` 竖版（544×960）
- `--jxl` 切换 Juggernaut XL 模型
- `--lora <文件名>` 加载 LORA（放入 `models\loras\`）
- `--lora-strength <数值>` LORA 权重，默认 **0.85**
- 用户说"优化细节"时，在不改变已选风格前提下微调 prompt 描述
