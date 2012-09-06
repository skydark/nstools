# My NScripter Tools

一些大概没有用了的与 NScript 有关的东西。

License: GPLv2

但 nstemplate.py 和 portable.py 除外。
它们并不依赖任何 GPL 项目，并且可以单独运行。
这两者均是 Public Domain 的。

* gbk2sjis.py 将简体 nscript.dat/00~99.txt 转换为日文编码。

    对不支持 GBK 而仅支持日文编码的 ONS 模拟器，当运行简体移植的时候会乱码。
    这个工具能将原脚本转换为日文编码。

    由于很多汉字在日文中并不存在，故会进行简繁转换和一些字符替换。
    部分无法自动处理的字符替换定义在 `gbk2sjis.dat` 中。

    使用方法：

    直接运行弹出 GUI 界面，选择要转换的脚本(自动判断是nscript.dat还是某个txt文件还是00~99.txt)。

    或
    `python gbk2sjis.py [选项] 原始文件/目录 [输出文件]`

    输出文件默认是当前目录下的 `out.txt` .

    选项除了帮助(`-h`)外只有一个：`-m auto/manual`，当出现无法转换的字符时是自动选择还是手动输入。
    自动选择是根据拼音选择的。

* onssaver.py 当替换脚本时根据新旧脚本的差异修复存档。

    NScripter 脚本更新后原有的存档会出现问题。这个工具在新旧脚本差异不大时修复存档。

    TODO(and never do)：改用 `difflib` 修复。

    使用方法：

    `python onssaver.py 原始脚本目录 新脚本目录 [存档文件]`

    如果不给出存档文件，默认为原始脚本目录中的所有 `save*.dat` 文件。

    新生成的存档会保存在新脚本目录中。

* nstemplate.py NS脚本模板。已抛弃。

    使用方法：

    直接执行 `python nstemplate.py` 获取帮助。

    运行 `python nstemplate.py nsttest.txt out.txt`，对比 `nsttext.txt` 和 `out.txt`.
