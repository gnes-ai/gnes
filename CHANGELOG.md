
# Release Note (`v0.0.24`)
> Release time: 2019-07-19 18:18:46


🙇 We'd like to thank all contributors for this new release! In particular,
 hanhxiao,  Jem,  Larry Yan,  felix,  🙇


### 🆕 New Features

 - [[```9f6c0524```](https://github.com/gnes-ai/gnes/commit/9f6c0524f986d735d3ef831fe2021579dff575c3)] __-__ __fasterrcnn__: add the original image to chunk list (*Jem*)
 - [[```abb0841c```](https://github.com/gnes-ai/gnes/commit/abb0841cdcd07c3bedeee03682b3022743449bda)] __-__ __encoder__: add convolution variational autoencoder (*Larry Yan*)

### 🐞 Bug fixes

 - [[```1b526832```](https://github.com/gnes-ai/gnes/commit/1b52683216a4bea57a5b9ac37b5b9c98e3586b30)] __-__ __base__: fix dump yaml kwargs (*hanhxiao*)
 - [[```086f3cea```](https://github.com/gnes-ai/gnes/commit/086f3cea723ac491c06f0630baf0809fa4afcc5e)] __-__ __base__: fix ump instance (*hanhxiao*)
 - [[```12dfde42```](https://github.com/gnes-ai/gnes/commit/12dfde423bcf0a2027c45328d16a03dd25cfe617)] __-__ __base__: move name setting to trainable base (*hanhxiao*)
 - [[```16f1a497```](https://github.com/gnes-ai/gnes/commit/16f1a497392ac484e1358863dcfc757fd1e74986)] __-__ __base__: move set config to metaclass (*hanhxiao*)
 - [[```b97acd6c```](https://github.com/gnes-ai/gnes/commit/b97acd6cc69d562c0577aeb86fda5f8301f9e26a)] __-__ __base__: fix duplicate warning (*hanhxiao*)
 - [[```991e4425```](https://github.com/gnes-ai/gnes/commit/991e4425ce1d650d0b2602df8abaab85f07c9b5f)] __-__ __base__: fix duplicate load and init from yaml (*hanhxiao*)
 - [[```69a486e5```](https://github.com/gnes-ai/gnes/commit/69a486e5092d0e5b7b0e84a907cd5a9294dc01b9)] __-__ __compose__: fix import (*hanhxiao*)
 - [[```4977aa3c```](https://github.com/gnes-ai/gnes/commit/4977aa3cf5e247c967c7b5d0729916fa69cc0381)] __-__ __vector indexer__: reorder relevance and chunk weight (*Jem*)
 - [[```2448411d```](https://github.com/gnes-ai/gnes/commit/2448411db6c21b5526fcc389c4e9112c09b11146)] __-__ __encoder__: modify CVAE (*Larry Yan*)
 - [[```b4bf0bf8```](https://github.com/gnes-ai/gnes/commit/b4bf0bf889cdfc11ae17146d08fa2544c4fd3a59)] __-__ __indexer__: add path check for dir and file (*hanhxiao*)
 - [[```92f36c33```](https://github.com/gnes-ai/gnes/commit/92f36c332354e32119eeb5c02cbd7e0c2c626d81)] __-__ __fasterrcnn__: handle imgs with 0 chunk (*Jem*)
 - [[```a1329913```](https://github.com/gnes-ai/gnes/commit/a13299132b776ccbb1826bf0f3a361e431a0f2ca)] __-__ __fasterrcnn__: fix bug for gpu (*Jem*)
 - [[```38eca0ce```](https://github.com/gnes-ai/gnes/commit/38eca0ceb7102d7076f7e3854b0154d85a2cd9c0)] __-__ __grpc__: change grpc client message size limit (*felix*)
 - [[```3836020a```](https://github.com/gnes-ai/gnes/commit/3836020aca4dbf9d3a650ca8c75907c2803db477)] __-__ __preprocessor__: fix preprocessor service handler function name error (*felix*)
 - [[```599a3c3d```](https://github.com/gnes-ai/gnes/commit/599a3c3dc4558bc34901189e54561e0f74bc2c19)] __-__ __compose__: fix composer logic (*hanhxiao*)
 - [[```7f3b2fb5```](https://github.com/gnes-ai/gnes/commit/7f3b2fb5eefa07c6fa3a119903afa6b1ad52cf75)] __-__ __release__: fix git tag version (*hanhxiao*)

### 🚧 Code Refactoring

 - [[```9bbb3c05```](https://github.com/gnes-ai/gnes/commit/9bbb3c0529ea92a947202bef1abfcd4a2f7bef77)] __-__ __compose__: move compose template to resources (*hanhxiao*)
 - [[```a4e153d7```](https://github.com/gnes-ai/gnes/commit/a4e153d7bddad52625a9ad5527024e0f2671f160)] __-__ __base__: remove dump path and reorganize work dir (*hanhxiao*)

### 🏁 Unit Test and CICD

 - [[```e088ea9c```](https://github.com/gnes-ai/gnes/commit/e088ea9c244265dbfc46326b3617371677f51262)] __-__ __drone__: turn off profiling in ci (*hanhxiao*)
 - [[```33a570b9```](https://github.com/gnes-ai/gnes/commit/33a570b9ba1dc1fa35917e1462c55e2b6926dc1b)] __-__ __drone__: remove pylint for faster ci (*hanhxiao*)
 - [[```51eafac7```](https://github.com/gnes-ai/gnes/commit/51eafac76d25c9442d1a63a2d2a431cbb00e2b44)] __-__ __indexer__: fix data path in unit test (*hanhxiao*)

### 🍹 Other Improvements

 - [[```43ef4108```](https://github.com/gnes-ai/gnes/commit/43ef4108e74afdf06ad8a84a29973f6bd739e2aa)] __-__ __git__: add tmp to ignore (*hanhxiao*)
 - [[```44b1a0c9```](https://github.com/gnes-ai/gnes/commit/44b1a0c976f6232708393c8c967d627da1d7df09)] __-__ fix unittest (*felix*)
 - [[```984a9a2d```](https://github.com/gnes-ai/gnes/commit/984a9a2d980f93bbac1c1b943fb6e6305bf03aaf)] __-__ __changelog__: update change log to v0.0.23 (*hanhxiao*)

# Release Note (`v0.0.23`)
> Release time: 2019-07-17 18:28:08


🙇 We'd like to thank all contributors for this new release! In particular,
 hanhxiao,  Jem,  felix,  Larry Yan,  Han Xiao,  🙇


### 🆕 New Features

 - [[```cb4d9cf2```](https://github.com/gnes-ai/gnes/commit/cb4d9cf2662e54cda14630ef6fdf0c2b954182d6)] __-__ __release__: add auto release and keep change log (*hanhxiao*)
 - [[```c667d874```](https://github.com/gnes-ai/gnes/commit/c667d874f35e5d4752b15688a893d5118b8ac606)] __-__ __image_preprocessor__: add fasterRCNN (*Jem*)
 - [[```a6c2975b```](https://github.com/gnes-ai/gnes/commit/a6c2975b2cb42791681349f3a09cec40794e0372)] __-__ __composer__: improve the gnes board with cards (*hanhxiao*)
 - [[```6ec4233d```](https://github.com/gnes-ai/gnes/commit/6ec4233d37c191705c406f035f5554d9333901b1)] __-__ __composer__: add swarm and bash generator (*hanhxiao*)
 - [[```08aa30f4```](https://github.com/gnes-ai/gnes/commit/08aa30f4c4a4467e25d32f0508fd01a80c7ee7c0)] __-__ __composer__: add shell script generator (*hanhxiao*)
 - [[```033a4b9c```](https://github.com/gnes-ai/gnes/commit/033a4b9c65bab6f9c392eedd9c4e3d233d00c3be)] __-__ __composer__: add composer and mermaid renderer (*hanhxiao*)

### 🐞 Bug fixes

 - [[```2b7c3f18```](https://github.com/gnes-ai/gnes/commit/2b7c3f180c6eb2b73378f24dd855ab44bef4e53d)] __-__ __compose__: resolve unclosed file warning (*hanhxiao*)
 - [[```8030feb2```](https://github.com/gnes-ai/gnes/commit/8030feb2d975460aa17c9cd1da56f69fba7f56c1)] __-__ __compose__: fix router logic in compose (*hanhxiao*)
 - [[```736f6053```](https://github.com/gnes-ai/gnes/commit/736f6053f0dc41ab9508bc49dfc4c3481060e5f3)] __-__ __gnesboard__: fix cdn (*hanhxiao*)
 - [[```fb07ff02```](https://github.com/gnes-ai/gnes/commit/fb07ff02fbd93cc07c570211bd0d5b6515ea6586)] __-__ __doc_reducer_router__: fix reduce error (*felix*)
 - [[```a7236308```](https://github.com/gnes-ai/gnes/commit/a7236308a834c2eb32686f00024ee31a405fedc1)] __-__ __image encoder__: define use_cuda variable via args (*felix*)
 - [[```cba5e190```](https://github.com/gnes-ai/gnes/commit/cba5e1905e272047481c41033474792f00b6da7a)] __-__ __image_encoder__: enable batching encoding (*felix*)
 - [[```3423ec83```](https://github.com/gnes-ai/gnes/commit/3423ec832c04aad22a6d897be36486e0cb3372a1)] __-__ __composer__: add compose api to api.py (*hanhxiao*)
 - [[```70ba3fca```](https://github.com/gnes-ai/gnes/commit/70ba3fca920ee15a26d1d2f6e8feacd263d3890b)] __-__ __composer__: in bash mode always run job in background (*hanhxiao*)
 - [[```054981ce```](https://github.com/gnes-ai/gnes/commit/054981ce11138fba59fec1fe69ee8e974585ece0)] __-__ __composer__: fix gnes board naming (*hanhxiao*)
 - [[```743ec3b0```](https://github.com/gnes-ai/gnes/commit/743ec3b06ec17f36c80e290fa2a2708e2fffba43)] __-__ __composer__: fix unit test and add tear down (*hanhxiao*)
 - [[```64aef413```](https://github.com/gnes-ai/gnes/commit/64aef41361814b4c0b58fe0d3e99d846f4b38c68)] __-__ __composer__: fix styling according to codacy (*hanhxiao*)
 - [[```dca4b03b```](https://github.com/gnes-ai/gnes/commit/dca4b03b5d610e164c17be8ddc4d2426ff8bd0d6)] __-__ __service__: fix bug grpc (*Larry Yan*)
 - [[```09e68da2```](https://github.com/gnes-ai/gnes/commit/09e68da21ca578ca28b62a179edc798343a42205)] __-__ __service__: fix grpc server size limit (*Larry Yan*)
 - [[```3da8da19```](https://github.com/gnes-ai/gnes/commit/3da8da19fd33ed5e3b3b5f50f55c46e74ecf5864)] __-__ __encoder__: rm un-used import in inception (*Larry Yan*)
 - [[```8780a4da```](https://github.com/gnes-ai/gnes/commit/8780a4da75f943e5f43499ec047f69c948fcac55)] __-__ bugs for integrated test (*Jem*)
 - [[```38fff782```](https://github.com/gnes-ai/gnes/commit/38fff78212b3bff88f1c5a3c5423011234e12e64)] __-__ __preprocessor__: move cv2 dep to pic_weight (*Han Xiao*)
 - [[```37155bba```](https://github.com/gnes-ai/gnes/commit/37155bbab0123d5e8071d82f66dbfb3b816d2413)] __-__ __preprocessor-video__: move sklearn dep to apply (*Han Xiao*)
 - [[```1f6a06a2```](https://github.com/gnes-ai/gnes/commit/1f6a06a292438b6d8ce440e0d60d600547ce159c)] __-__ __encoder__: rm tf inception unittest (*Larry Yan*)
 - [[```eaffbbff```](https://github.com/gnes-ai/gnes/commit/eaffbbfffc40799e02c38a678b7e9d4344be4147)] __-__ __encoder__: register tf inception in __init__ (*Larry Yan*)
 - [[```d0099b79```](https://github.com/gnes-ai/gnes/commit/d0099b7957bb16b96d45af37bfaa75d95863729e)] __-__ __encoder__: add necessary code from tf (*Larry Yan*)
 - [[```b480774a```](https://github.com/gnes-ai/gnes/commit/b480774a51f8ce5406295a44ae641fe18343d106)] __-__ __encoder__: add inception tf (*Larry Yan*)

### 📗 Documentation

 - [[```54276c6a```](https://github.com/gnes-ai/gnes/commit/54276c6a175a30fb69947e007bbc8082f7f7bb18)] __-__ __readme__: improve readme image and structure (*hanhxiao*)

### 🏁 Unit Test and CICD

 - [[```1dcfdfa7```](https://github.com/gnes-ai/gnes/commit/1dcfdfa725cc269369ce1d7d7c8f83a3f5c2240c)] __-__ __docker-image__: optimze docker file (*felix*)
 - [[```bda562d1```](https://github.com/gnes-ai/gnes/commit/bda562d18866f9ac8f26a4f6ea588303c80c7d53)] __-__ __drone__: auto release with cron job (*hanhxiao*)

### 🍹 Other Improvements

 - [[```0c737a94```](https://github.com/gnes-ai/gnes/commit/0c737a944e3edef97bcf94ea5d35bedf0483795f)] __-__ __release__: revert back master check (*hanhxiao*)
 - [[```7b04697c```](https://github.com/gnes-ai/gnes/commit/7b04697cf4eb48c1b86ee59260a073b8ad8066e2)] __-__ __changelog__: revert the change log to empty (*hanhxiao*)
 - [[```d02f320d```](https://github.com/gnes-ai/gnes/commit/d02f320daceeeb87492e748e960f323856d093a1)] __-__ revert docker file (*felix*)
