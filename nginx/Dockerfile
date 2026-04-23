FROM nginx:alpine

# 配置文件从项目根目录复制（Dockerfile 在 nginx/ 子目录）
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 前端文件从项目根目录复制
COPY frontend/ /usr/share/nginx/html/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
