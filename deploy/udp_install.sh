#!/bin/bash

DIR="$( cd "$( dirname "$0" )" && pwd )"
cd ${DIR}
source ${DIR}/env_settings.sh

if [[ $? != 0 ]]; then
    exit 1
fi

function download(){
    wget $1
    if [[ $? != 0 ]]; then
        echo "download $1 failed"
    fi
}

function init_umc(){
    #export ALL_RPM=`curl "http://10.186.18.20:666?version=${VERSION}&linux=7&release=qa"|grep rpm|awk -F "FTP_ADDR}/" '{print $2}' 2>/dev/null`
    export ALL_RPM=`cat rpm_version/${VERSION} 2>/dev/null`
    if [[ $? != 0 ]]; then
       exit 1
    fi

    # install umc
    export HAS_UMC=0
    for RPM in `echo ${ALL_RPM}`
    do
        #echo ${RPM}| grep "umc-[0-9]*.[0-9]*.[0-9]*.[0-9]*-qa.x86_64.rpm" >/dev/null
        echo ${RPM}| grep "umc-[0-9]*.[0-9]*.[0-9]*.[0-9]*-qa.coverage.x86_64.rpm" >/dev/null
        if [[ $? == 0 ]]; then
            export HAS_UMC=1
            rpm -ivh ${FTP_URL}/${RPM} --prefix=${UMC_HOME}
            if [[ $? != 0 ]]; then
                exit 1
            fi
            break
        fi
    done
    if [[ ${HAS_UMC} != 1 ]];then
        echo "umc not found"
        exit 1
    fi

    #download components
    cd ${UMC_HOME}/components && rm -rf *
    for RPM in `echo ${ALL_RPM}`
    do
        download ${FTP_URL}/${RPM}
    done

    #download mysql and mongodb
    download ${FTP_URL}/mysql-tarball/mysql-5.7.21-linux-glibc2.12-x86_64.tar.gz
    #download ${FTP_URL}/mysql-tarball/mysql-5.6.26-linux-glibc2.5-x86_64.tar.gz
    download ${FTP_URL}/mysql-tarball/mysql-5.7.25-linux-glibc2.12-x86_64.tar.gz
    download ${FTP_URL}/mysql-tarball/mongodb-linux-x86_64-3.4.9.tgz

    # modify data json
    modify_data_json "ucore"
    modify_data_json "uagent"
    modify_data_json "ustats"
    modify_data_json "udeploy"
    modify_data_json "uguard-agent"
    modify_data_json "uguard-mgr"
    modify_data_json "urman-agent"
    modify_data_json "urman-mgr"
}

function start_umc(){
    echo ""
    echo "start umc"
    cd ${UMC_HOME}
    nohup ./bin/umc
    if [[ $? != 0 ]]; then
	    exit 1
    fi
    echo "start umc success"
    echo ""
}

function modify_data_json(){
    export RPM=`ls ${UMC_HOME}/components|grep "$1-[0-9]*.[0-9]*.[0-9]*.[0-9]*-qa.x86_64.rpm"`
    if [[ $? != 0 ]]; then
	    exit 1
    fi
    sed -i "s/$1-[0-9]*.[0-9]*.[0-9]*.[0-9]*-qa.x86_64.rpm/${RPM}/g" ${DIR}/udp_install.json
}


function main(){
    init_umc
    start_umc
    sleep 5
    python ${DIR}/udp_install.py ${UMC_ADDR} ${UMC_PORT} ${DIR}/udp_install.json
}

main
