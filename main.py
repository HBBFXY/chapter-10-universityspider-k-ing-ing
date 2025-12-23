import requests
from bs4 import BeautifulSoup
import time
import random
import csv
from requests.exceptions import RequestException
from urllib3.exceptions import InsecureRequestWarning

# 忽略SSL警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class ChinaUniversityRankSpider:
    def __init__(self):
        # 基础配置
        self.base_url = "https://www.shanghairanking.cn/rankings/bcur/2024"  # 2024软科中国大学排名
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.shanghairanking.cn/",
            "Connection": "keep-alive"
        }
        self.all_universities = []  # 存储所有高校数据
        self.timeout = 10  # 请求超时时间
        self.retry_times = 3  # 重试次数
        self.delay_range = (1, 3)  # 随机延时范围（秒）

    def get_page_content(self, url):
        """获取单页内容（带重试机制）"""
        for attempt in range(self.retry_times):
            try:
                # 随机延时，避免反爬
                time.sleep(random.uniform(*self.delay_range))
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                    verify=False  # 忽略SSL验证（根据实际情况调整）
                )
                response.raise_for_status()  # 抛出HTTP错误
                response.encoding = response.apparent_encoding  # 自动识别编码
                return response.text
            except RequestException as e:
                print(f"第{attempt+1}次请求失败：{e}")
                if attempt == self.retry_times - 1:
                    print(f"页面{url}请求失败，跳过该页")
                    return None

    def get_total_pages(self):
        """获取总页数"""
        html = self.get_page_content(self.base_url)
        if not html:
            return 1  # 默认1页
        
        soup = BeautifulSoup(html, "html.parser")
        # 定位分页控件（根据目标网站结构调整）
        pagination = soup.find("div", class_="pagination")
        if not pagination:
            return 1
        
        # 提取最后一页的页码
        page_links = pagination.find_all("a", class_="page-link")
        if not page_links:
            return 1
        
        # 过滤出数字页码，取最大值
        page_numbers = []
        for link in page_links:
            try:
                num = int(link.get_text(strip=True))
                page_numbers.append(num)
            except ValueError:
                continue
        
        return max(page_numbers) if page_numbers else 1

    def parse_page(self, html):
        """解析单页高校数据"""
        if not html:
            return []
        
        soup = BeautifulSoup(html, "html.parser")
        # 定位数据表格（根据目标网站结构调整）
        table = soup.find("table", class_="rk-table")
        if not table:
            return []
        
        rows = table.find("tbody").find_all("tr")
        page_data = []
        
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue
            
            # 提取字段（排名、学校名称、省份、总分）
            rank = cols[0].get_text(strip=True)  # 排名
            name = cols[1].get_text(strip=True)  # 学校名称
            province = cols[2].get_text(strip=True)  # 省份
            score = cols[3].get_text(strip=True)  # 总分
            
            university_info = {
                "排名": rank,
                "学校名称": name,
                "省份": province,
                "总分": score
            }
            page_data.append(university_info)
        
        return page_data

    def crawl_all_pages(self):
        """爬取所有页面数据"""
        total_pages = self.get_total_pages()
        print(f"开始爬取，共{total_pages}页数据")
        
        for page in range(1, total_pages + 1):
            # 构造分页URL（根据目标网站分页规则调整）
            # 软科排名分页参数为?page=页码
            page_url = f"{self.base_url}?page={page}"
            print(f"正在爬取第{page}/{total_pages}页：{page_url}")
            
            html = self.get_page_content(page_url)
            page_data = self.parse_page(html)
            
            if page_data:
                self.all_universities.extend(page_data)
                print(f"第{page}页爬取成功，获取{len(page_data)}条数据")
            else:
                print(f"第{page}页无有效数据")
        
        print(f"爬取完成！共获取{len(self.all_universities)}条高校数据")

    def save_to_csv(self, filename="中国大学排名2024.csv"):
        """将数据保存为CSV文件"""
        if not self.all_universities:
            print("无数据可保存")
            return
        
        # 定义CSV表头
        headers = ["排名", "学校名称", "省份", "总分"]
        
        with open(filename, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(self.all_universities)
        
        print(f"数据已保存至：{filename}")

if __name__ == "__main__":
    # 实例化并执行爬虫
    spider = ChinaUniversityRankSpider()
    spider.crawl_all_pages()
    spider.save_to_csv()
