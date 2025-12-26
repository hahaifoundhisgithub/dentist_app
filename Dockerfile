FROM nginx:alpine

# 把剛剛寫好的設定檔複製進去，蓋掉預設的
COPY nginx.conf /etc/nginx/nginx.conf