# garlicFileNameChanger（大蒜君的文件名修改器）
GarlicFileNameChanger（大蒜君的文件名修改器）发布说明

v1.0：
一个能够批量修改文件名称的python脚本，支持用户自行输入剧集名称后自动提取集数进行规范化命名，以方便私有云及各类播放器自动识别匹配剧集。运行环境python 3.10.1，v1.0版本支持功能清单如下：
1. 支持单一文件夹下的所有文件自动命名
2. 支持提取[]、【】、()、点分以及无特殊符号五种命名规范的剧集数
3. 支持提取S01E01格式的识别，新命名将以剧集名称_第01季_第01集.xxx的方式呈现
4. 支持单集多分段格式的识别，包括abc、上中下两种分段命名，新命名将以剧集名称_第01季_第01集_上.xxx的方式呈现
5. 支持文件名修改预览，确认无误后才会正式执行修改动作
6. 支持剧集连续性校验，按集数数字顺序检测，在改名前会提示用户缺失的剧集
7. 提取剧集数失败、新文件名命名存在冲突时，均会提示用户

v1.1：
1. 增加自定义季数文本设置功能，会在未能自动识别匹配到文件名中的季数信息时，询问用户是否需要在新文件名中增加自定义季数文本

感谢DeepSeek在研发过程中的大力支持
