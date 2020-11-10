# UMC auto test with casperjs
  环境需求：一台Docker,内部安装至少4个子docker，分别为umc-1,umc-2,umc-3,umc-4...................

    用途:    Casperjs_autotest :  作为运行casperjs的测试代码机器（创建文件请查收附件docker-compose.yml）
                umc-1：作为安装DMP平台的机器

    运行步骤：
            Step1:  创建外部docker: Casperjs_autotest
                    文件： ./umc_autotesting/compose/docker-compose.yml ，是创建外部docker文件

            Step2:  在 Casperjs_autotest 内创建 7个子docker

                    文件：./umc_autotesting/composeFile/innerdocker/docker-compose.yml ，是创建7个子docker文件

            Step3:  运行 all_start.sh 文件，在umc-1上安装DMP以及初始换DMP,并且运行测试脚本
                        文件： ./umc_autotesting/test_suits/all_start.sh， 内包含在umc-1上安装DMP以及初始换DMP环境,并且运行测试脚本
                        all_start.sh文件命令解析：
                           1）.从服务器下载最新版本DMP组件到umc-1上，并且安装umc组件：casperjs test Init_udp.js  --pre=../includes/Initdmp.js |tee ./log/Init_udp.log 2>&1  &&
                           2）.初始化DMP环境：casperjs test Init_udp_config.js --pre=../includes/Initdmp.js |tee ./log/Init_udp_config.log 2>&1  &&
                           3）.运行自动化测试脚本: casperjs test  --pre=../includes/setup.js  XXX

            Step4:  销毁Casperjs_autotest 内的7个子docker

Usage example:
use test mode which correspond with mock data:
./all_start.sh
