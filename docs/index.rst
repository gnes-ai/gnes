.. GNES documentation master file, created by
   sphinx-quickstart on Tue Apr 30 14:53:34 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

GNES is Generic Neural Elastic Search
=====================================

.. image:: ../.github/gnes-github-banner.png
   :align: center

|
GNES *jee-nes* is **Generic Neural Elastic Search**, a cloud-native semantic search system based on deep neural network.

GNES enables large-scale index and semantic search for **text-to-text**, **image-to-image**, **video-to-video** and *any-to-any* content form.


Highlights
----------

.. raw:: html

   <center>
   <table>
     <tr>
       <th><h3>☁️</h3><h3>Cloud-Native & Elastic</h3></th>
       <th><h3>🐣</h3><h3>Easy-to-Use</h3></th>
       <th><h3>🔬</h3><h3>State-of-the-Art</h3></th>
     </tr>
     <tr>
       <td width="33%"><sub>GNES is <i>all-in-microservice</i>! Encoder, indexer, preprocessor and router are all running in their own containers. They communicate via versioned APIs and collaborate under the orchestration of Docker Swarm/Kubernetes etc. Scaling, load-balancing, automated recovering, they come off-the-shelf in GNES.</sub></td>
       <td width="33%"><sub>How long would it take to deploy a change that involves just switching a layer in VGG? In GNES, this is just one line change in a YAML file. We abstract the encoding and indexing logic to a YAML config, so that you can change or stack encoders and indexers without even touching the codebase.</sub></td>
       <td width="33%"><sub>Taking advantage of fast-evolving AI/ML/NLP/CV communities, we learn from best-of-breed deep learning models and plug them into GNES, making sure you always enjoy the state-of-the-art performance.</sub></td>
     </tr>
     <tr>
         <th><br><h3>🌌</h3><h3>Generic & Universal</h3></th>
         <th><br><h3>📦</h3><h3>Model as Plugin</h3></th>
         <th><br><h3>💯</h3><h3>Best Practice</h3></th>
       </tr>
       <tr>
         <td width="33%"><sub>Searching for texts, image or even short-videos? Using Python/C/Java/Go/HTTP as the client? Doesn't matter which content form you have or which language do you use, GNES can handle them all. </sub></td>
         <td width="33%"><sub>When built-in models do not meet your requirments, simply build your own with <i>one Python file and one YAML file</i>. No need to rebuilt GNES framework, as your models will be loaded as plugins and directly rollout online.</sub></td>
         <td width="33%"><sub>We love to learn the best practice from the community, helping our GNES to achieve the next level of availability, resiliency, performance, and durability. If you have any ideas or suggestions, feel free to contribute.</sub></td>
       </tr>
   </table>
   </center>

|
|


.. toctree::
   :maxdepth: 3
   :caption: GNES Microservices API

   chapter/microservice.rst


.. toctree::
   :maxdepth: 3
   :caption: GNES Modules

   api/gnes

.. toctree::
   :maxdepth: 1
   :caption: Miscs

   chapter/troubleshooting.md
   chapter/protobuf-dev.md
   chapter/enviromentvars.md
   chapter/swarm-tutorial.md

.. toctree::
   :maxdepth: 2
   :caption: Contributing

   chapter/CONTRIBUTING.md

.. toctree::
   :maxdepth: 1
   :caption: Changelog

   chapter/CHANGELOG.md


Tutorials
---------

.. warning::
   🚧 Tutorial is still under construction. Stay tuned! Meanwhile, we sincerely welcome you to contribute your own learning experience / case study with GNES!



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
