# 如何挂机让软件自迭代？有这个Skill就可以了！

## 背景

之前CC等编程工具遭人诟病的点在于对于难以长期专注，以完成大型项目的生成，写着写着可能就会忘东忘西。整体看起来像个样子，但细看一堆问题，需要人类码农帮忙纠正、擦屁股。

但拐点在于25年11月 Claude Code opus 4.5的发布，其结合CC让人们看到其不止是简单搓个Demo，还可以端到端完整的交付xW行的大颗粒需求甚至整个项目。

紧接着就是诸如GLM4.7、Minimaxi-m25等追随者，让这一能力得到进一步普及

我们码农得面对一个现实：

AI Coder会带来**X倍效率提升**已经是个进行时。问题是这个**X**是多少？我们又应该如何提升**X**大小？



**当前方式**：

即是打磨下需求文档、设计文档交于CC让其直接开发，为避免Vibe coding带来的漂移，中间还需多轮交互、纠偏，最后让其补充测试用例进行验证，再手动测试签收。期间会有**大量需要人介入**的点，人成为整个系统的瓶颈，影响**Scaling up**



**演进方向**：

**自迭代、长任务**+**SDD**(*Spec-Driven Development* )即是版本答案

前者解决无论需求多复杂，如何让**程序一直跑下去**直至交付的问题

后者解决Vibe coding的漂移，交付质量的问题

这点，早在Anthropic的[effective-harnesses-for-long-running-agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)给出了解决方向

**目标态**：

需求设计阶段重度参与、打磨 -> 自开发自迭代 -> 确认交付内容，点击签收

这样就可以**并行N个项目**，实现**Scaling up**



## Long Task Skill

基于此，借助CC+opus开发了一套严格遵从SDD、TDD，并能一直编码直至完成（或者你tokens耗尽）的SKILL。



先看它能干什么：

先看效果：



以上基于CC+opus，技术选型langchain





同样一份原始需求，基于CC+GLM4.7 -5.0又开发了一版，技术选型也为langchain





还没完，基于CC+minimax-m25，再开发了一版，此次选型为Spring AI





共计消耗tokens约为10亿上下



### 全流程严格遵从SDD，告别Vibe coding“抽卡”

![](images\4.png)

在经历多轮需求、设计澄清，形成需求文档、设计文档、UCD文档等必要项后，会初始化一套由Spec文档、进度跟踪文档以及校准脚本构成的、确保严格按照SDD流程进行的环境。

![image-20260304001708432](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260304001708432.png)

其中init等脚本、feature级设计文档、测试文档等均是llm根据项目内容，自行生成。

![image-20260304010138154](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260304010138154.png)

![image-20260304010202598](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260304010202598.png)



之后，在`long-task-guide`指引下，会按照`feature-list.json`拆分的需求逐一实现

![image-20260304002033453](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260304002033453.png)

完成的状态为`passing`，未完成的未`failing`，以此驱动完成自我迭代开发



### 多轮需求、设计、UCD澄清

![image-20260304004719101](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260304004719101.png)

![image-20260304004800332](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260304004800332.png)

![image-20260304004816617](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260304004816617.png)

需求分析——多轮澄清，SRS审批



![image-20260304004839166](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260304004839166.png)

![image-20260304004849672](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260304004849672.png)

UCD澄清&审批(追求最佳效果，建议采用Figma+CC实践)

![image-20260304005139620](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260304005139620.png)

![image-20260304005219781](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260304005219781.png)

设计澄清&多套技术选型择优，设计文档审批

期间可以就需求、UCD、设计等任何问题进行打断、追问，以及自行修改输出文档，以打磨确认为所需开发内容。

之后Skill会将以上文档作为Spec关键文档基线化，用于指导后续迭代开发

*需求、设计文档模板可自定义，默认采用默认模板*



### 迭代流程严格遵从TDD，告别给AI”擦屁股“


![](images\5.png)

为确保feature开发过程中的质量，全开发流程严格遵从TDD，同时不仅看**UT覆盖率**，还加入了变异测试，确保**UT有效性**

TDD开发完成后，会进行一次**特性级ST验证**，其中包含集成测试、结合UI的黑盒验证

各个阶段，都会通过**脚本**确保该阶段目标有无达成



其会**主动**找用户补充必要配置项：大模型的key、数据库账号密码等用于开发、验证：

![image-20260304010504762](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260304010504762.png)

![image-20260304010624297](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260304010624297.png)

所有必要项Ready后会创建特性级设计文档&st用例集

![image-20260304011214762](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260304011214762.png)

![image-20260304011255186](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260304011255186.png)



最后feature开发完成，用户会收到开发总结，以决定签收继续开发下个特性，还是打回让其补充|重构其他内容

![9d161d46ee42f0090743b7e4474de27b](http://gitee.com/null_161_0561/picpic/raw/master/2021/9d161d46ee42f0090743b7e4474de27b.jpg)







### 自验证



请首先自行安装必要的`Chrome Dev Mcp`，Skill会通过引导、脚本等确保`Chrome Dev Mcp`正常进行UI验证



### 修Bug，并自回归





### 任何阶段中断，都可无缝衔接回来

只需输入`继续`

![image-20260304003957784](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260304003957784.png)

![image-20260304004014568](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260304004014568.png)

![image-20260304004028014](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260304004028014.png)

脚本会自动向claude.md注入引导项，即使上下文丢失，也会继续开发下个特性。意味着可以在流程中任何点上中断



### 无限挂机直至完成

![image-20260304004100740](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260304004100740.png)

通过`auto_loop.py`脚本，可实现无限挂机，直至需求完成，或者tokens耗尽

**建议**：每个feature迭代开发完，人工介入查看完成情况，确定是否验收通过

**注意**：该脚本存在较高风险，会自动忽视告警，不能保障开发质量与系统安全，酌情使用



### For AI——协助外部AI快速了解本项目

![image-20260304011833458](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260304011833458.png)



所有这些，只需要简单一句：

```shell
以下为我的原始需求，请使用`long task skill`进行开发:
XXXXX
```



哪些交给LLM，哪些交给脚本固化，这是决定Skill优劣的标尺



## 感谢：

本项目借鉴了[Superpower Skill](https://github.com/obra/superpowers)，这是一个非常优秀的严格遵从TDD的软件工程Skill