# adcode 爬虫

## 数据来源

> http://www.stats.gov.cn/tjsj/tjbz/tjyqhdmhcxhfdm/2018/

## docker 运行

```
docker build -t patsnap/adcode-crawler:0.0.1 .
docker run -v /path/to/adcode-crawler:/usr/app -it patsnap/adcode-crawler:0.0.1
```