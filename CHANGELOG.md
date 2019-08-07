
# Release Note (`v0.0.26`)
> Release time: 2019-08-02 18:18:45


🙇 We'd like to thank all contributors for this new release! In particular,
 hanhxiao,  Jem,  Larry Yan,  🙇


### 🆕 New Features

 - [[```d0b2ef0b```](https://github.com/gnes-ai/gnes/commit/d0b2ef0b1c8d781e558d1a7f0d7708c355f09d37)] __-__ __composer__: more interaction for gnes board (*hanhxiao*)
 - [[```9c33dc66```](https://github.com/gnes-ai/gnes/commit/9c33dc66a2d1eb478138851ebb0fa27ebfcad9c5)] __-__ __router__: allow consecutive mapping and reducing ops (*hanhxiao*)

### 🐞 Bug fixes

 - [[```fc5026da```](https://github.com/gnes-ai/gnes/commit/fc5026da1ee0021abfefcefaee2ec41c0583b2c2)] __-__ __board__: improve gnes board 500 message (*hanhxiao*)
 - [[```823bdeda```](https://github.com/gnes-ai/gnes/commit/823bdeda9ead30ae989a8c46cb32a51581bc4753)] __-__ __test__: fix grpc gentle shutdown (*hanhxiao*)
 - [[```f6a801f7```](https://github.com/gnes-ai/gnes/commit/f6a801f7b18a5df435335778deaba790df09526c)] __-__ __test__: fix preprocessor building for image test (*hanhxiao*)
 - [[```50fdc041```](https://github.com/gnes-ai/gnes/commit/50fdc0414659d7fe0acf858fe23e67c1be1bee0b)] __-__ __base__: fix ref to CompositionalTrainableBase (*hanhxiao*)
 - [[```54a931c7```](https://github.com/gnes-ai/gnes/commit/54a931c78345617014229792d9e9ac6ca6ae4f71)] __-__ __test__: fix test images by removing mac stuff (*hanhxiao*)
 - [[```14cdfabe```](https://github.com/gnes-ai/gnes/commit/14cdfabed5bb1ac8e75f1944f31323c69df6d9d8)] __-__ __sliding window__: fix the boundary (*Jem*)
 - [[```46b5c94e```](https://github.com/gnes-ai/gnes/commit/46b5c94eea4973e3f1b2dcb05e85981f316a4ca3)] __-__ __encoder__: fix name for video encoder (*Larry Yan*)
 - [[```15eb50b4```](https://github.com/gnes-ai/gnes/commit/15eb50b4d1a85e3b3ddd8ceeb7e3fd0b2b45b428)] __-__ __encoder__: fix params in basevideo encoder (*Larry Yan*)
 - [[```5b0fe7c6```](https://github.com/gnes-ai/gnes/commit/5b0fe7c6c3c5f2fa433c090fdad9c8c80d59f4df)] __-__ __preprocessor__: fix FFmpegVideoSegmentor (*Larry Yan*)
 - [[```d6a46fa6```](https://github.com/gnes-ai/gnes/commit/d6a46fa6b6a931b4dc0e334f5a89bb66460a84b0)] __-__ __encoder__: fix import path for mixture encoder (*Larry Yan*)
 - [[```17779676```](https://github.com/gnes-ai/gnes/commit/17779676bd452b2679ba7e64918721cf85e0bec1)] __-__ __encoder__: fix mixture encoder (*Larry Yan*)
 - [[```95f03c56```](https://github.com/gnes-ai/gnes/commit/95f03c56701f4a691f8412490f6dcf9565751da1)] __-__ __encoder__: fix bug in video mixture encoder (*Larry Yan*)
 - [[```3fdf1c06```](https://github.com/gnes-ai/gnes/commit/3fdf1c06e302a5c3e32d28de431e076802ff5c9e)] __-__ __encoder__: fix mixture (*Larry Yan*)
 - [[```67991533```](https://github.com/gnes-ai/gnes/commit/679915336a2d3d99041844717723e8a06dae5899)] __-__ __encoder__: add netvlad and netfv register class (*Larry Yan*)
 - [[```92500f0f```](https://github.com/gnes-ai/gnes/commit/92500f0f1451914a7c68efdd71158b8cd03103c1)] __-__ __encoder__: add netvlad and netfv (*Larry Yan*)

### 🚧 Code Refactoring

 - [[```c430ef64```](https://github.com/gnes-ai/gnes/commit/c430ef64eaa6960a9768b006c1959630ae4f18d4)] __-__ __base__: better batch_size control (*hanhxiao*)
 - [[```58217d8c```](https://github.com/gnes-ai/gnes/commit/58217d8cd3deaad6dbca6e8683e5baeea370593f)] __-__ __base__: moving is_trained to class attribute (*hanhxiao*)
 - [[```7126d496```](https://github.com/gnes-ai/gnes/commit/7126d496e1195c7469e417672329145e326d5c1c)] __-__ __preprocessor__: separate resize logic from the unary preprocessor (*hanhxiao*)
 - [[```52f87c7f```](https://github.com/gnes-ai/gnes/commit/52f87c7fa2d54b25a6b075cf549ce960ed63b59d)] __-__ __base__: make pipelineencoder more general and allow pipelinepreprocessor (*hanhxiao*)

### 📗 Documentation

 - [[```3ab3723e```](https://github.com/gnes-ai/gnes/commit/3ab3723e9f1fc9b095ad6d7a808330d47d28f2c6)] __-__ __tutorial__: fix image and code layout (*hanhxiao*)

### 🍹 Other Improvements

 - [[```635ba37f```](https://github.com/gnes-ai/gnes/commit/635ba37f6970bb0c2d5cb3919df673d0327a9593)] __-__ __changelog__: update change log to v0.0.25 (*hanhxiao*)

# Release Note (`v0.0.25`)
> Release time: 2019-07-26 19:45:21


🙇 We'd like to thank all contributors for this new release! In particular,
 hanhxiao,  felix,  Larry Yan,  Jem,  Han Xiao,  Felix,  🙇


### 🆕 New Features

 - [[```66aec9c9```](https://github.com/gnes-ai/gnes/commit/66aec9c94ae44486a56fbc9c8667e18c24e01c51)] __-__ __grpc__: add StreamCall and decouple send and receive (*hanhxiao*)
 - [[```5697441b```](https://github.com/gnes-ai/gnes/commit/5697441bca859a56d986b6c540ddb1fae0d3b258)] __-__ __indexer__: consider offset relevance at query time (*Jem*)
 - [[```04c9c745```](https://github.com/gnes-ai/gnes/commit/04c9c74556be8dd343de1cdb6375dc744d4da531)] __-__ __image preprocessor__: calculate offsetnd for each chunk (*Jem*)
 - [[```b34a765a```](https://github.com/gnes-ai/gnes/commit/b34a765aa851ccabf45f73a740e82b95de3f1c1a)] __-__ __compose__: add interactive mode of GNES board using Flask (*hanhxiao*)
 - [[```5876c15e```](https://github.com/gnes-ai/gnes/commit/5876c15ea3285cec62fbfe17872594c48f7e043f)] __-__ __base__: support loading external modules from py and yaml (*hanhxiao*)

### 🐞 Bug fixes

 - [[```a20672d3```](https://github.com/gnes-ai/gnes/commit/a20672d3be6306fc339f9a4523047e4491ebf1b8)] __-__ __preprocessor__: add logging in helper module (*felix*)
 - [[```f9500c1f```](https://github.com/gnes-ai/gnes/commit/f9500c1fe09dcbe27bec8a7a690e9fb243d51cc4)] __-__ __protobuffer__: add doc_type as func argument in RequestGenerator (*felix*)
 - [[```1c3bb01a```](https://github.com/gnes-ai/gnes/commit/1c3bb01a2c87717d3a342c86a65592ea78ad717d)] __-__ __service__: fix bug in doc_type name in indexer service (*Larry Yan*)
 - [[```d834f578```](https://github.com/gnes-ai/gnes/commit/d834f578218ee38d4984ec8243b2d77aa6bb65ba)] __-__ __service__: add doc type to req generator (*Larry Yan*)
 - [[```80e234e1```](https://github.com/gnes-ai/gnes/commit/80e234e154caea53b9103007ffc1cd669cd00bc7)] __-__ __service__: fix bug in req Generator add doc_type (*Larry Yan*)
 - [[```5743e258```](https://github.com/gnes-ai/gnes/commit/5743e2582f36236d20188afee9ed2972de46be28)] __-__ __indexer__: fix bug in indexer service (*Larry Yan*)
 - [[```11dde2bf```](https://github.com/gnes-ai/gnes/commit/11dde2bf9eb5ba0a673551bf061ae56c5601c75c)] __-__ __encoder__: fix bug in tf inception (*Larry Yan*)
 - [[```ded92c57```](https://github.com/gnes-ai/gnes/commit/ded92c578b9aed43085ce12b0d81084f8dc5acbc)] __-__ __indexer__: fix bug for indexer service dealing with empty doc (*Larry Yan*)
 - [[```1dff06f1```](https://github.com/gnes-ai/gnes/commit/1dff06f18e4ab13d416db2ec5ab173cbcf325931)] __-__ __encoder__: fix bug for encoder service dealing with empty doc (*Larry Yan*)
 - [[```7e43d5a2```](https://github.com/gnes-ai/gnes/commit/7e43d5a295ae7b7217f2c32658d6c4c60fe285e1)] __-__ __preprocessor__: fix ffmpeg to deal with broken image (*Larry Yan*)
 - [[```83ebaced```](https://github.com/gnes-ai/gnes/commit/83ebacedc37e6fccb8726799e36c37241018f22e)] __-__ __preprocessor__: move import imagehash to inside (*hanhxiao*)
 - [[```7c669a70```](https://github.com/gnes-ai/gnes/commit/7c669a7075142c9e3bb161f4649646b07b772b45)] __-__ __test__: rename the yaml test file (*hanhxiao*)
 - [[```2cc26342```](https://github.com/gnes-ai/gnes/commit/2cc2634299ab36e784305c419903fbed8a38349e)] __-__ __compose__: change textarea font to monospace (*hanhxiao*)
 - [[```e644e391```](https://github.com/gnes-ai/gnes/commit/e644e3916222d18a9ebe0329fd600b6f776fb69a)] __-__ __encoder__: fix gpu limitation in inception (*Larry Yan*)
 - [[```89d8b70c```](https://github.com/gnes-ai/gnes/commit/89d8b70c9e8df6b2de55e7668bab88e67466e21f)] __-__ __grpc__: fix bug in RequestGenerator query (*Larry Yan*)
 - [[```c52c2cc6```](https://github.com/gnes-ai/gnes/commit/c52c2cc69239a89b5aeba473ef8a6c0fc48ea744)] __-__ __base__: fix gnes_config mixed in kwargs (*hanhxiao*)
 - [[```68c15fac```](https://github.com/gnes-ai/gnes/commit/68c15fac3d7d32cb9f32de620bc930206b18b2f7)] __-__ __base__: fix redundant warning in pipeline encoder (*hanhxiao*)
 - [[```aadeeefb```](https://github.com/gnes-ai/gnes/commit/aadeeefbe2b3ee29ea6882194fa4631b3dd99ff5)] __-__ __composer__: fix composer state machine (*hanhxiao*)
 - [[```c0bffe6c```](https://github.com/gnes-ai/gnes/commit/c0bffe6cc363050721c87b4c4912ebf1d2e03437)] __-__ __indexer__: normalize weight (*Jem*)
 - [[```2c696483```](https://github.com/gnes-ai/gnes/commit/2c6964837c4bc7387b0585d26b4f8ab5f80d3909)] __-__ __indexer__: fix weight in indexer call (*Larry Yan*)
 - [[```139a02d9```](https://github.com/gnes-ai/gnes/commit/139a02d91983a07eac4d8a9650b1ab48946fc864)] __-__ __compose__: fix compose bug of pub-sub rule, duplicate yaml_path (*hanhxiao*)
 - [[```649ed131```](https://github.com/gnes-ai/gnes/commit/649ed1314b9c12167a958d6f8e259944ebdf96e3)] __-__ __encoder__: add normalize option in cvae encoder (*Larry Yan*)
 - [[```eb487799```](https://github.com/gnes-ai/gnes/commit/eb487799b3e4b602738765d9ad5edea997147930)] __-__ __encoder__: fix tf scope error in cvae encoder (*Larry Yan*)
 - [[```ab6c88cc```](https://github.com/gnes-ai/gnes/commit/ab6c88ccfe54ba5f96f09510e97b9658c553c1a9)] __-__ __encoder__: fix error in cvae encoder (*Larry Yan*)
 - [[```a4b883ac```](https://github.com/gnes-ai/gnes/commit/a4b883acb312b5f47d34955d3ec2dccb4cd782c6)] __-__ __indexer__: add drop raw bytes option to leveldb (*Larry Yan*)
 - [[```4b52bcba```](https://github.com/gnes-ai/gnes/commit/4b52bcbaff84f48ffaf0903ca8e8f3d63a67c09c)] __-__ __grpc__: fix grpc plugin path (*Larry Yan*)
 - [[```d3fbbcac```](https://github.com/gnes-ai/gnes/commit/d3fbbcacf64ebe1a1e40fa3afaefac09b6eeb943)] __-__ __weighting__: add simple normalization to chunk search (*Jem*)
 - [[```08a9a4e3```](https://github.com/gnes-ai/gnes/commit/08a9a4e3863afde2dbcb74633c1648e92c47abb5)] __-__ __grpc__: fix grpc service (*Larry Yan*)
 - [[```6e6bbf83```](https://github.com/gnes-ai/gnes/commit/6e6bbf834933b2fa04ab6c62c3c64421b6fed360)] __-__ __grpc__: add auto-gen grpc code (*Larry Yan*)
 - [[```b89d8fa2```](https://github.com/gnes-ai/gnes/commit/b89d8fa297717d8aa033dc51cd5c1c7ae83bf30b)] __-__ __grpc__: add stream index and train in proto (*Larry Yan*)
 - [[```15cd7e58```](https://github.com/gnes-ai/gnes/commit/15cd7e58f0032464bc6a5d24e536a3ef63e6a3ea)] __-__ __base__: fix dump and load on compositional encoder (*hanhxiao*)
 - [[```bab48919```](https://github.com/gnes-ai/gnes/commit/bab48919e847e2c55217ea40e56557023ce6cb41)] __-__ __encoder__: fix tf inception (*Larry Yan*)
 - [[```973672ef```](https://github.com/gnes-ai/gnes/commit/973672ef7041d9a04ea77694e503a5e5c419bde0)] __-__ __encoder__: fix bug for encoder bin load (*Larry Yan*)
 - [[```1bef3971```](https://github.com/gnes-ai/gnes/commit/1bef3971dcbe8b35a7ddcfcbdd29011a7f2dc7c0)] __-__ __setup__: fix setup script (*hanhxiao*)
 - [[```67fb5766```](https://github.com/gnes-ai/gnes/commit/67fb5766b61bcbe0aa5ffdc6706cf5085e2446d7)] __-__ __compose__: fix argparser (*hanhxiao*)
 - [[```63c4515f```](https://github.com/gnes-ai/gnes/commit/63c4515ff96fdb9f354cd935ded21b1db691a037)] __-__ __compose__: accept parser argument only (*hanhxiao*)
 - [[```887d89cc```](https://github.com/gnes-ai/gnes/commit/887d89cc2d99720a94260ea113584b4d1c472ea4)] __-__ __release__: ask BOT_URL before releasing (*hanhxiao*)

### 🚧 Code Refactoring

 - [[```9973f600```](https://github.com/gnes-ai/gnes/commit/9973f60065d8127bdc236e547faa2f44c4eb9afd)] __-__ __preprocessor__: rename singleton to unary (*hanhxiao*)
 - [[```a1a2b020```](https://github.com/gnes-ai/gnes/commit/a1a2b020ccd99f3e80d0adaad9e8c68c1220d592)] __-__ __proto__: refactor request stream call (*hanhxiao*)

### 📗 Documentation

 - [[```c853e3da```](https://github.com/gnes-ai/gnes/commit/c853e3dae989ce2365b4b3cf0b37f8c54dc6b767)] __-__ __tutorial__: fix svg size (*hanhxiao*)
 - [[```04cccdcd```](https://github.com/gnes-ai/gnes/commit/04cccdcd93c77cc4e9cb8b3f3e773c2c67353875)] __-__ __tutorial__: fix svg path (*hanhxiao*)
 - [[```8927cd4f```](https://github.com/gnes-ai/gnes/commit/8927cd4fb073b5f21bf5b73fe7f10ca8524f1dad)] __-__ __tutorial__: add yaml explain (*hanhxiao*)
 - [[```5b52ce4c```](https://github.com/gnes-ai/gnes/commit/5b52ce4c4b077ced8a6962d97f4e3fcee23513e6)] __-__ fix doc path (*hanhxiao*)
 - [[```45751e1f```](https://github.com/gnes-ai/gnes/commit/45751e1f9b360c0247152b13f31a24f98de4a6e6)] __-__ __readme__: add quick start for readme (*hanhxiao*)
 - [[```73891ecc```](https://github.com/gnes-ai/gnes/commit/73891ecc1e14b8ff1ef45a2165f51c320aa68fc8)] __-__ __readme__: add install guide to readme and contribution guide (*hanhxiao*)

### 🏁 Unit Test and CICD

 - [[```6ff3079b```](https://github.com/gnes-ai/gnes/commit/6ff3079be798437d65315e56996812c3aa44e926)] __-__ __unittest__: skip all os environ test (*hanhxiao*)
 - [[```816fa043```](https://github.com/gnes-ai/gnes/commit/816fa04397648a8b97adbd92a924762cea3ca0d0)] __-__ __unittest__: skip blocked test (*hanhxiao*)
 - [[```79a9c106```](https://github.com/gnes-ai/gnes/commit/79a9c10649324921e9a748f73cb8ccc68b29e410)] __-__ __unittest__: run test in verbose mode (*hanhxiao*)
 - [[```83276f90```](https://github.com/gnes-ai/gnes/commit/83276f90a6544a279ac2c60d5caca029d1d67f2e)] __-__ __torchvision__: install torchvision dependency to enable tests (*hanhxiao*)
 - [[```499682ce```](https://github.com/gnes-ai/gnes/commit/499682ce942c5fac778d8c09f40f95606439114d)] __-__ __base__: add unit test for load a dumped pipeline from yaml (*hanhxiao*)
 - [[```26a7ad18```](https://github.com/gnes-ai/gnes/commit/26a7ad1867fe3c9d22bad94abdc435dc38fac4c3)] __-__ __composer__: add unit test for flask (*hanhxiao*)
 - [[```87ec1fd2```](https://github.com/gnes-ai/gnes/commit/87ec1fd21b759a2476cd863f08cbad0327ab67a8)] __-__ __base__: move module delete to teardown (*hanhxiao*)
 - [[```479b183d```](https://github.com/gnes-ai/gnes/commit/479b183d3996865439b17b531c13356a4ec02000)] __-__ __compose__: skip unit test (*hanhxiao*)

### 🍹 Other Improvements

 - [[```c30f39cc```](https://github.com/gnes-ai/gnes/commit/c30f39ccfcafc014acf196a97f53c82d3532b09b)] __-__ ... (*felix*)
 - [[```2d5654c0```](https://github.com/gnes-ai/gnes/commit/2d5654c0466408251ede54a1eadf25a4e2e567bc)] __-__ __license__: add license (*hanhxiao*)
 - [[```d3347910```](https://github.com/gnes-ai/gnes/commit/d3347910b7048a8b41c7d3c11093fbf34ef9efe1)] __-__ reformat code and optimize import (*hanhxiao*)
 - [[```71491ffb```](https://github.com/gnes-ai/gnes/commit/71491ffb5e5de3497b98ad4f4c411cc6c12abd26)] __-__ __changelog__: update change log to v0.0.24 (*hanhxiao*)

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
