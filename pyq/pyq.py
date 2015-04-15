#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    author  : 陈小雪
#    date    : 2015-04-01 10:13:31
#    email   : chellychen@yeah.net
#    version : 1.0.1


from pyquery import PyQuery as pq
import urllib
import urllib2
import os
import json
import sys
import codecs
import re
reload(sys)
sys.setdefaultencoding("utf-8")
base_url = 'http://www.zhihu.com/'
zhuanlan_url = "http://zhuanlan.zhihu.com/api/columns"
limit = 10
#zhuanlan_url = "http://zhuanlan.zhihu.com/api/columns/career/posts?limit=10&offset=90"

class Download():
    query_list = [
        {
            "sort":"question",
            "desc":"问题",
            "link_query":"a.question_link",
            "desc_query":"div#zh-question-detail div.zm-editable-content",
            "author_query":"h3.zm-item-answer-author-wrap",
            "content_query":"div.zm-editable-content.clearfix",
            "user_name":"span.name",
            "title_query":"h2.zm-item-title.zm-editable-content"
        },
        {
            "sort":"zhuanlan",
            "desc":"专栏",
            "link_query":"a.link",
            "desc_query":"div.description ng-binding",
            "author_query":"div.title.ng-binding",
            "user_name":"span.name",
            "article_query":"a.ng-binding",
            "title_query":"h1.entry-title.ng-binding",
            "content_query":"section.entry-content.ng-binding",
            "time_query":"time.published.ng-binding.ng-isolate-scope"
        }
    ]

    def load_config(self):
        if not os.path.isfile("config"):
            os.mknod("config")

        try:
            self.cfg = json.loads("config")
        except:
            self.cfg = { }

    def save_config(self):
        with open("config","w") as f:
            json.dump(self.cfg,f)

    def start(self):
        self.load_config()
        self.url = None
        self.sort = None
        if len(sys.argv) > 2:
            for i,argv in enumerate(sys.argv):
                if argv == "--url":
                    self.url = base_url + sys.argv[i + 1]
                if argv == "--sort":
                    self.sort = sys.argv[i + 1]
        flag = 0

        if not self.url or  not self.sort:
            print "此脚本用于分析知乎上用户关注问题列表而下载个问题答案，要求提供用户的url和sort"
            print "usage:"
            print "pyp.py --url url --sort sort"
            return 0

        for query in self.query_list:
            if query["sort"]  == self.sort:
                self.user_name = query["user_name"]
                self.link_query = query["link_query"]
                self.desc_query = query["desc_query"]
                self.author_query = query["author_query"]
                self.article_query = query.get("article_query"," ")
                self.title_query = query.get("title_query"," ")
                self.content_query = query.get("content_query"," ")
                self.time_query = query.get("time_query"," ")
                self.desc = query.get("desc"," ")
                flag = 1
                break
        if flag == 1:
            self.download()
            self.save_config()
        else:
            print "本脚本支持以下类型文章："
            for query in self.query_list:
                print query["sort"],":",query["desc"]
            print "  "
            print "您输入的分类无效"

    def load_doc(self):
        self.doc = pq(url = self.url)

    def load_url(self,url):
        try:
            data = urllib2.urlopen(url).read()
            data = json.loads(data)
        except:
            #raise Exception('load url:%s false!'%url)
            print 'load url:%s false!'%url
            return None
        return data

    def get_question_url(self):
        lists = [ ]
        links = self.doc(self.link_query)

        for target in links:
            href = pq(target).attr("href")
            if href.startswith("http:"):
                url = href
            elif href.startswith("/"):
                url = "/".join(base_url.split("/")[0:3]) + href
            else:
                url = base_url + href

            lists.append(url)
        
        self.filter_url(lists)
        self.user_name = self.doc(self.user_name).text().encode('raw_unicode_escape').decode('utf-8','ignore')
        
        print self.user_name,":关注的",self.desc,"收集完成",len(self.urls)

    def filter_url(self,urls):
        tmp = [ ]
        tmp = filter(lambda x:x.find(self.sort) != -1,urls)
        self.urls = tmp
    
    def download(self):
        self.load_doc()
        self.get_question_url()

        print "开始下载",self.desc
        for url in self.urls:
            print url
            if self.sort == "question":
                self.download_question(url)
            elif self.sort == "zhuanlan":
                self.download_cloumn(url)

    def download_question(self,url):
        doc = pq(url = url)
        title = doc(self.title_query).text().encode('raw_unicode_escape').decode('utf-8','ignore')
        desc = doc(self.desc_query).text().encode('raw_unicode_escape').decode('utf-8','ignore')
        f = codecs.open(title+".txt","wb+","utf-8")

        title = title + "\r\n"
        title = title + "========================================================"
        title = title + "\r\n\r\n"
        content = title + desc +"\r\n\r\n"

        texts = doc(self.content_query)
        for t in texts:
            text = pq(t)
            try:
                text = text.remove("noscript").html()\
                        .replace("<br>","\n")\
                        .replace("<br/>","\n")\
                        .replace("<br \>","\n")\
                        .replace("<p>","\n")\
                        .replace("</p>","\n")
                text = re.sub("<[^>]*>",'', text)
                text += "\n>>>>>>>>>>>\n\n"

                content += text.encode('raw_unicode_escape').decode('utf-8','ignore')
            except:
                print "the content_query is not right or url in not right"
                f.close()
                return -1

        f.write(content+ "\n\n")
        f.close()
        print "下载完成"

    def download_cloumn(self,url):
        urls = self.collect_cloum_url(url)
        column = url.split("/")[-1]

        print "下载 %s"%self.cfg.get(column," ")

        if not os.path.exists(column):
            os.mkdir(column)

        for url in urls:
            article_id = url.split("/")
            u = url.split("/")
            u.insert(2,"posts")
            url = zhuanlan_url + "/".join(u)
            article_id = u[-1]

            print url
            
            data = self.load_url(url)
            if not data:continue
            title = data.get("title")
            self.cfg[article_id] = title
            content = data.get("content")
            self.save_data(column,article_id,content)
            
        print "下载完成"
            

    def collect_cloum_url(self,url):
        urls = [ ]
        key = url.split("/")[-1]
        url = "%s/%s/posts?limit=%s&offset="%(zhuanlan_url,key,limit)
        offset = 0
        d = None
        
        while 1:
            open_url = url + str(offset)
            data = self.load_url(open_url)
            if not data:continue
            for d in data:
                urls.append(d.get("url"))

            if len(data) < 10:
                break
            offset += 10
        
        if d:
            name = d.get("column", {}).get("name")
            print name,"专栏文章搜集完成"
        self.cfg[key] = name
        return urls

    def save_data(self,dirs,title,content):
        filename = os.path.join(dirs,title)
        f = open(filename,"w")
        f.write(content)
        f.close()

if __name__ == "__main__":
    Download().start()

