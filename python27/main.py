#!/usr/bin/env python
# -*- coding: utf-8 -*-

import webapp2
from google.appengine.api import urlfetch
import json
import jinja2
import collections

templateLoader = jinja2.FileSystemLoader(searchpath="templates/") # このディレクトリーからテンプレートを読み込む設定が含まれているオブジェクトを作る。
templateEnv = jinja2.Environment(loader=templateLoader) # テンプレートを上のtemplateLoaderを使って読み込む環境を用意する。
pataTmpl = templateEnv.get_template("pata.html") # パタトクカシーー用のテンプレートを"pata.htmlから読み込む。
networkTmpl = templateEnv.get_template("norikae.html")  # 乗換案内用のテンプレートを"norikae.html"から読み込む。

networkJson = urlfetch.fetch("https://tokyo.fantasy-transit.appspot.com/net?format=json").content  # ウェブサイトから電車の線路情報をJSON形式でダウンロードする
network = json.loads(networkJson.decode('utf-8'))  # JSONとしてパースする（stringからdictのlistに変換する）

# このRequestHandlerでパタトカシーーのリクエストを処理して、結果を返す。
class Root(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/html; charset=UTF-8'
    self.response.write('''
<h1>Hello!</h1>
  <ul>
    <li><a href=/pata>パタトクカシーー</a></li>
    <li><a href=/norikae>乗換案内</a></li>
  </ul>
''')

# このRequestHandlerでパタトカシーーのリクエストを処理して、結果を返す。
class Pata(webapp2.RequestHandler):
    def get(self):
        # とりあえずAとBをつなぐだけで返事を作っていますけど、パタタコカシーーになるように自分で直してください！
        # pata = self.request.get("a") + self.request.get("b")
        pata = ""
        for i in range(max(len(self.request.get("a")), len(self.request.get("b")))): # 文字列の長さが長い方をとってくる
            if i < len(self.request.get("a")): 
                pata += self.request.get("a")[i] 
            if i < len(self.request.get("b")):
                pata += self.request.get("b")[i]

        self.response.headers['Content-Type'] = 'text/html; charset=UTF-8'
        # テンプレートの内容を埋め込んで、返事を返す。
        self.response.write(pataTmpl.render(pata=pata, request=self.request))

class Norikae(webapp2.RequestHandler):
    def setGraph(self, network):
        graph = dict()
        for line in network:
            for i in range(len(line["Stations"])):
                if line["Stations"][i] in graph.keys():# line["Stations"][i]がgraphにすでに入っているかどうか
                    if i != 0: # 先頭じゃなかったら一つ前の駅を隣接リストに入れる
                        graph[line["Stations"][i]].append(line["Stations"][i - 1])
                    if i != len(line["Stations"]) - 1: # 最後じゃなかったら一つ後を隣接リストに入れる
                        graph[line["Stations"][i]].append(line["Stations"][i + 1])
                else:
                    if i != 0: # 先頭じゃなかったら一つ前の駅を隣接リストに入れる
                        # graph.setdefault(line["Stations"][i], []).append(line["Stations"][i - 1])
                        graph[line['Stations'][i]] = [line['Stations'][i-1]]
                    if i != len(line["Stations"]) - 1: # 最後じゃなかったら一つ後を隣接リストに入れる
                        # graph.setdefault(line["Stations"][i], []).append(line["Stations"][i + 1])
                        graph[line['Stations'][i]] = [line['Stations'][i+1]]
        return graph

    def bfs(self, origin, destination):
        graph = self.setGraph(network)
        visited = set()
        queue = collections.deque()
        pre_station_dict = dict() # ルートを格納

        queue.append(origin)  # 現在地を探索候補キューに格納
        pre_station_dict[origin] = [origin] # 出発地を格納

        # キューが空になるまで
        while queue:

            vertex = queue.popleft() # キューから次の探索地点を一つ取り出す
   
            for neighbor in graph[vertex]: # 現在地から次に行けるポイントを調べる
                if neighbor == destination:
                    pre_station_dict[neighbor] = pre_station_dict[vertex]  + [neighbor]
                    return pre_station_dict[neighbor]

                elif neighbor not in visited:
                    pre_station_dict[neighbor] = pre_station_dict[vertex] + [neighbor]
                    visited.add(neighbor) # 「探索済みリスト」に取り出した地点を格納
                    queue.append(neighbor)
                  
        return []
         
    def get(self):
        # 本当は入力したものを探索するようにしたいけどできない
        # route = self.bfs(self.request.get("origin").decode('utf-8'), self.request.get("destination").decode('utf-8'))
        route = self.bfs(network[0]["Stations"][0], network[0]["Stations"][6]) # 品川と原宿
        self.response.headers['Content-Type'] = 'text/html; charset=UTF-8'
        self.response.write(networkTmpl.render(route=route, request=self.request))

app = webapp2.WSGIApplication([
    ('/', Root),
    ('/pata', Pata),
    ('/norikae', Norikae),
], debug=True)
