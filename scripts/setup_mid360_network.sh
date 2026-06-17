#!/bin/bash
set -e

IFACE=${1:-eth0}
HOST_IP=${2:-192.168.1.50}

echo "=== 配置 MID360 有线网口 ==="
echo "网口: $IFACE"
echo "主机IP: $HOST_IP/24"

sudo ip addr flush dev $IFACE || true
sudo ip addr add ${HOST_IP}/24 dev $IFACE
sudo ip link set $IFACE up

echo "=== 当前网口信息 ==="
ip addr show $IFACE

echo "=== 扫描 192.168.1.0/24 网段 ==="
sudo arp-scan --interface=$IFACE 192.168.1.0/24 || true

echo "=== 测试常见 MID360 IP ==="
ping -c 2 192.168.1.2 || true
ping -c 2 192.168.1.145 || true
ping -c 2 192.168.1.156 || true
