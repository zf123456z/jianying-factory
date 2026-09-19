"""剪映工厂 - 口播一键成片
从文案到成片的完整流水线：
1. 读取文案
2. TTS生成配音
3. 自动分镜
4. 匹配素材
5. 生成字幕
6. 铺BGM
7. 导出成片
"""
import os, json, argparse

class VoiceoverBuilder:
    """口播视频成片构建器"""
    
    def __init__(self, script_path, assets_dir, output_dir):
        self.script_path = script_path
        self.assets_dir = assets_dir
        self.output_dir = output_dir
        self.segments = []
        
    def read_script(self):
        """读取口播文案"""
        with open(self.script_path, encoding="utf-8") as f:
            text = f.read().strip()
        # 按段落/句号分镜
        import re
        self.segments = [s.strip() for s in re.split(r'[。！？\n]', text) if s.strip()]
        print(f"文案共 {len(self.segments)} 段")
        return self.segments
    
    def list_assets(self):
        """列出可用素材"""
        exts = ('.mp4', '.mov', '.avi', '.jpg', '.png', '.mp3', '.wav')
        assets = []
        for f in os.listdir(self.assets_dir):
            if f.lower().endswith(exts):
                assets.append(os.path.join(self.assets_dir, f))
        print(f"找到 {len(assets)} 个素材")
        return assets
    
    def build(self):
        """执行完整成片流程"""
        print("=== 剪映工厂：口播成片开始 ===")
        self.read_script()
        assets = self.list_assets()
        
        plan = {
            "segments": self.segments,
            "assets_available": assets,
            "total_segments": len(self.segments),
            "estimated_duration": len(self.segments) * 5,  # 每段约5秒
        }
        
        plan_path = os.path.join(self.output_dir, "edit_plan.json")
        os.makedirs(self.output_dir, exist_ok=True)
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        
        print(f"编辑计划已生成: {plan_path}")
        print(f"预计时长: {plan['estimated_duration']}秒")
        print("=== 下一步：通过GUI自动化执行剪辑 ===")
        return plan

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="剪映工厂 - 口播成片")
    p.add_argument("--script", required=True, help="文案文件路径")
    p.add_argument("--assets", required=True, help="素材文件夹路径")
    p.add_argument("--output", required=True, help="输出目录")
    args = p.parse_args()
    builder = VoiceoverBuilder(args.script, args.assets, args.output)
    builder.build()
