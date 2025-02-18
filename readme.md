This is a project for CSC575/CSC475 
This project aims to This project aims to develop a Live MIDI Performance & Visualization System that combines real-time MIDI music generation from a computer keyboard or MIDI controller with a dynamic visualizer for live performances, DJ sets, or interactive music shows.

Users will be able to play MIDI notes using a standard keyboard, generate loops and beats, and see real-time animations that respond to the music. The visualizations will be synchronized with MIDI input, making it a useful tool for electronic musicians, DJs, and VJs (visual jockeys).



1. Pixel Art to Melody（像素图转旋律）
用户在 网格 上绘制像素点，系统自动转换为 8-bit 旋律。
纵轴（Y 轴）：决定音高（高处 = 高音，低处 = 低音）。
横轴（X 轴）：决定播放顺序，从左到右依次播放。
仅使用 Square Wave（方波），所有音符都是相同音色。

2. 网格音符编辑（可调节旋律长度）
网格列数可调节（16、32、48 等），影响旋律长度。
BPM（播放速度） 自动适应网格列数变化，确保节奏感一致。
交互方式：
单击：放置/删除音符（像素点）。

3. 复古游戏音源选择（Chip Emulation）
用户可以选择不同的 8-bit 经典音源芯片，调整方波音质：
NES (2A03) – 经典红白机风格。
Game Boy (LR35902) – 更柔和的 8-bit 音色。
Commodore 64 (SID Chip) – 音色更丰富，带滤波器。
选择不同芯片后，系统自动调整音轨风格。

4. 预设像素艺术旋律
内置经典像素图（如 超级玛丽、洛克人），用户可以试听并编辑旋律。
支持保存 & 载入 用户修改的像素旋律作品。










1. 标题 & 作者信息
标题：可以暂定为 “PixelTone: An 8-bit Music Sequencer Based on Pixel Art”
作者：列出你们团队成员的姓名和联系方式


2. ABSTRACT（摘要）
你可以先写一个简要的摘要，包括以下内容：
背景：像素艺术和 8-bit 音乐的结合在游戏和复古音乐制作中广受欢迎。
目标：本项目旨在开发一个交互式 8-bit 音乐编曲工具，通过绘制像素图来生成 8-bit 风格的旋律。
方法：使用 Pygame 构建网格界面，并使用 Square Wave 作为唯一音色，以 NES/Game Boy 等经典音源风格进行模拟。
预期贡献：为音乐创作者和游戏开发者提供一个直观的音乐创作工具。


3. INTRODUCTION（引言）
可以扩展以下内容：
音乐信息检索（MIR）背景：介绍 8-bit 音乐的特点，特别是在游戏音乐和电子音乐中的应用。
动机：为什么使用像素艺术作为音乐创作方式？有哪些现有工具？本项目如何改进用户体验？
目标：
设计一个基于像素艺术的音乐编曲工具。
仅使用 Square Wave，符合经典 8-bit 风格。
允许用户调整 BPM、网格长度，并支持不同 8-bit 经典音源芯片（NES/Game Boy 等）。


4. METHODS（方法）
你可以先从以下几个方面描述：

系统架构
介绍项目的技术架构（Pygame 实现 UI，Web Audio API 处理声音，可能的存储方式）。

像素图与旋律映射
网格系统：X 轴 = 时间，Y 轴 = 音高。
用户交互：单击/拖拽放置音符，BPM 自适应网格变化。

声音生成
Pygame + Square Wave 生成 8-bit 音色。
不同芯片模拟（NES、Game Boy、Commodore 64）。


5. EXPECTED RESULTS & EVALUATION（预期结果 & 评估）
描述项目的评估方式，比如：
生成的旋律是否符合 8-bit 风格？
用户体验（是否易于使用？音乐创作是否直观？）
音乐作品的多样性（是否能创造不同风格的 8-bit 音乐？）


6. CONCLUSION & FUTURE WORK（总结与未来工作）
总结：简要概述 PixelTone 的核心功能和贡献。
未来发展：
增加 MIDI 导出功能。
增加 AI 生成模式，让用户可以自动生成 8-bit 音乐。
增强音色系统，支持更多波形。

7. REFERENCES（参考文献）
如果你们参考了任何文献、开源项目或其他相关研究，可以在此处列出。