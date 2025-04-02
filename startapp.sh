#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 恢复默认颜色

# 显示横幅
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}       RSS to Feishu 部署脚本       ${NC}"
echo -e "${BLUE}============================================${NC}"

# 获取本机IP地址
get_ip() {
    ip_address=$(hostname -I | awk '{print $1}')
    if [ -z "$ip_address" ]; then
        ip_address="localhost"
    fi
    echo "$ip_address"
}

# 检查Docker是否安装
check_docker() {
    echo -e "${BLUE}[1/5]${NC} 检查Docker环境..."
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}[错误]${NC} Docker未安装，请先安装Docker"
        echo -e "Ubuntu: ${YELLOW}sudo apt-get update && sudo apt-get install docker.io -y${NC}"
        echo -e "CentOS: ${YELLOW}sudo yum install -y docker${NC}"
        exit 1
    else
        docker_version=$(docker --version | awk '{print $3}' | sed 's/,//')
        echo -e "${GREEN}[成功]${NC} 检测到Docker版本: $docker_version"
    fi

    # 检查Docker服务是否运行
    if ! docker info &> /dev/null; then
        echo -e "${YELLOW}[警告]${NC} Docker服务未运行，尝试启动..."
        sudo systemctl start docker
        if ! docker info &> /dev/null; then
            echo -e "${RED}[错误]${NC} 无法启动Docker服务，请手动检查"
            exit 1
        fi
        echo -e "${GREEN}[成功]${NC} Docker服务已启动"
    fi
}

# 检查Docker Compose是否安装
check_docker_compose() {
    echo -e "${BLUE}[2/5]${NC} 检查Docker Compose环境..."
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}[错误]${NC} Docker Compose未安装，请先安装Docker Compose"
        echo -e "安装方法: ${YELLOW}pip install docker-compose${NC} 或参考Docker官方文档"
        exit 1
    else
        compose_version=$(docker-compose --version | awk '{print $3}' | sed 's/,//')
        echo -e "${GREEN}[成功]${NC} 检测到Docker Compose版本: $compose_version"
    fi
}

# 准备配置文件
prepare_config() {
    echo -e "${BLUE}[3/5]${NC} 准备配置文件..."
    
    # 创建配置文件（如果不存在）
    if [ ! -f config.json ]; then
        echo '{
    "webhook_url": "",
    "interval": 60,
    "sources": []
}' > config.json
        echo -e "${GREEN}[成功]${NC} 已创建初始化配置文件"
    else
        echo -e "${GREEN}[成功]${NC} 配置文件已存在"
    fi

    # 创建sent_entries.json文件（如果不存在）
    if [ ! -f sent_entries.json ]; then
        echo '{}' > sent_entries.json
        echo -e "${GREEN}[成功]${NC} 已创建初始化发送记录文件"
    else
        echo -e "${GREEN}[成功]${NC} 发送记录文件已存在"
    fi
    
    # 创建日志文件（如果不存在）
    touch rss_feishu.log
    echo -e "${GREEN}[成功]${NC} 已准备日志文件"
}

# 构建并启动服务
build_and_start() {
    echo -e "${BLUE}[4/5]${NC} 构建并启动服务..."
    
    # 检查Dockerfile是否存在
    if [ ! -f Dockerfile ]; then
        echo -e "${RED}[错误]${NC} Dockerfile不存在，无法构建镜像"
        exit 1
    fi
    
    # 检查docker-compose.yml是否存在
    if [ ! -f docker-compose.yml ]; then
        echo -e "${RED}[错误]${NC} docker-compose.yml不存在，无法启动服务"
        exit 1
    fi
    
    # 构建镜像
    echo -e "${YELLOW}正在构建镜像...${NC}"
    if ! docker-compose build; then
        echo -e "${RED}[错误]${NC} 构建镜像失败，请检查Dockerfile"
        exit 1
    fi
    
    # 启动服务
    echo -e "${YELLOW}正在启动服务...${NC}"
    if ! docker-compose up -d; then
        echo -e "${RED}[错误]${NC} 启动服务失败，请检查docker-compose.yml"
        exit 1
    fi
    
    echo -e "${GREEN}[成功]${NC} 服务已成功启动"
}

# 显示服务状态和提示信息
show_status() {
    echo -e "${BLUE}[5/5]${NC} 检查服务状态..."
    
    # 获取容器状态
    container_status=$(docker-compose ps)
    echo -e "${YELLOW}服务状态：${NC}"
    echo "$container_status"
    
    # 验证服务是否正常运行
    if docker-compose ps | grep "Up" &> /dev/null; then
        ip_addr=$(get_ip)
        echo -e "\n${GREEN}[成功]${NC} RSS到飞书推送服务已成功启动！"
        echo -e "请访问 ${GREEN}http://$ip_addr:5000${NC} 进行配置"
        echo -e "日志文件: ${YELLOW}rss_feishu.log${NC}"
        echo -e "\n管理命令:"
        echo -e "  - 查看日志: ${YELLOW}docker-compose logs -f${NC}"
        echo -e "  - 重启服务: ${YELLOW}docker-compose restart${NC}"
        echo -e "  - 停止服务: ${YELLOW}docker-compose down${NC}"
        echo -e "  - 更新服务: ${YELLOW}docker-compose down && docker-compose up -d${NC}"
    else
        echo -e "\n${RED}[警告]${NC} 服务可能未正常启动，请检查日志"
        echo -e "查看日志: ${YELLOW}docker-compose logs${NC}"
    fi
}

# 添加命令行参数支持
case "$1" in
    start)
        check_docker
        check_docker_compose
        prepare_config
        build_and_start
        show_status
        ;;
    stop)
        echo -e "${BLUE}停止服务...${NC}"
        docker-compose down
        echo -e "${GREEN}[成功]${NC} 服务已停止"
        ;;
    restart)
        echo -e "${BLUE}重启服务...${NC}"
        docker-compose restart
        echo -e "${GREEN}[成功]${NC} 服务已重启"
        ;;
    status)
        echo -e "${BLUE}服务状态:${NC}"
        docker-compose ps
        ;;
    logs)
        echo -e "${BLUE}查看日志:${NC}"
        docker-compose logs -f
        ;;
    update)
        echo -e "${BLUE}更新服务...${NC}"
        git pull
        docker-compose down
        docker-compose build
        docker-compose up -d
        echo -e "${GREEN}[成功]${NC} 服务已更新并重启"
        ;;
    *)
        if [ -z "$1" ]; then
            # 默认执行完整流程
            check_docker
            check_docker_compose
            prepare_config
            build_and_start
            show_status
        else
            echo -e "${BLUE}RSS to Feishu 服务管理脚本${NC}"
            echo -e "用法: $0 [选项]"
            echo -e "\n选项:"
            echo -e "  ${GREEN}start${NC}    - 启动服务"
            echo -e "  ${GREEN}stop${NC}     - 停止服务"
            echo -e "  ${GREEN}restart${NC}  - 重启服务"
            echo -e "  ${GREEN}status${NC}   - 查看服务状态"
            echo -e "  ${GREEN}logs${NC}     - 查看服务日志"
            echo -e "  ${GREEN}update${NC}   - 更新代码并重启服务"
            echo -e "\n不带参数则执行完整的检查和启动流程"
        fi
        ;;
esac 