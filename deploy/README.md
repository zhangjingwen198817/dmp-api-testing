## 使用说明
### 构建 docker 环境
1. compose文件在compose目录下，配置不再做额外说明，可自行修改

### 配置环境
* 修改目录下env_setting.sh 文件, 里面配置了version，安装目录(若修改，需同步修改udp_install.json)，暂不建议修改安装目录

### 批量安装组件
* 修改udp_install.json 文件，为json格式，支持使用umc的批量json，脚本会自动修改对应rpm包版本

### quick start
1. `make docker_up` 执行docker-compose up (安装)
2. `make install` 在对应的容器中执行下载组件，安装umc ，和启动umc
3. `make clean` 执行docker-compose down (卸载)


