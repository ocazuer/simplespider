import socket
import ssl
import requests
from lxml import html


def log(*args, **kw):
    # print(*args, **kw)
    pass


class Model(object):
    def __repr__(self):
        class_name = self.__class__.__name__
        properties = (u'{} = ({})'.format(k, v)
                      for k, v in self.__dict__.items())
        r = u'\n<{}:\n  {}\n>'.format(class_name, u'\n  '.join(properties))
        return r


class Movie(Model):
    def __init__(self):
        self.ranking = 0
        self.name = ''
        self.staff = ''
        self.publish_info = ''
        # self.rating = 0
        # self.quote = ''
        self.number_of_comments = 0


def parsed_url(url):
    # 检查协议
    protocol = 'http'
    if url[:7] == 'http://':
        u = url.split('://')[1]
    elif url[:8] == 'https://':
        protocol = 'https'
        u = url.split('://')[1]
    else:
        # '://' 定位 然后取第一个 / 的位置来切片
        u = url

    # 默认 path
    i = u.find('/')
    if i == -1:
        host = u
        path = '/'
    else:
        host = u[:i]
        path = u[i:]

    # 检查端口
    port_dict = {
        'http': 80,
        'https': 443,
    }
    # 默认端口
    port = port_dict[protocol]
    if host.find(':') != -1:
        h = host.split(':')
        host = h[0]
        port = int(h[1])
    return protocol, host, port, path


def socket_by_protocol(protocol):
    """
    返回一个 socket 实例
    """
    if protocol == 'http':
        s = socket.socket()
    else:
        s = ssl.wrap_socket(socket.socket())
    return s


def response_by_socket(s):
    """
    参数是一个 socket 实例
    返回这个 socket 读取的所有数据
    """
    response = b''
    buffer_size = 1024
    while True:
        r = s.recv(buffer_size)
        if len(r) == 0:
            break
        response += r
    return response


def parsed_response(r):
    header, body = r.split('\r\n\r\n', 1)
    h = header.split('\r\n')
    status_code = h[0].split()[1]
    status_code = int(status_code)

    headers = {}
    for line in h[1:]:
        k, v = line.split(': ')
        headers[k] = v
    return status_code, headers, body


def get(url):
    """
    用 GET 请求 url 并返回响应
    """
    protocol, host, port, path = parsed_url(url)

    s = socket_by_protocol(protocol)
    s.connect((host, port))

    request = 'GET {} HTTP/1.1\r\nhost: {}\r\nUser-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36\r\nConnection: close\r\n\r\n'.format(
        path, host)
    encoding = 'utf-8'
    s.send(request.encode(encoding))

    response = response_by_socket(s)
    log('response', response)
    r = response.decode(encoding)

    status_code, headers, body = parsed_response(r)
    if status_code == 301:
        url = headers['Location']
        return get(url)
    return status_code, headers, body


def movie_from_div(div):
    movie = Movie()

    names = div.xpath('.//span[@class="title"]/text()')
    movie.name = ''.join(names)
    movie.ranking = div.xpath('.//div[@class="pic"]/em')[0].text
    # movie.rating = div.xpath('.//span[@class="rating_num"]')[0].text
    # movie.quote = div.xpath('.//span[@class="inq"]')[0].text
    infos = div.xpath('.//div[@class="bd"]/p/text()')
    movie.staff, movie.publish_info = [i.strip() for i in infos[:2]]
    movie.number_of_comments = div.xpath('.//div[@class="star"]/span')[-1].text[:-3]
    return movie


def movies_from_url(url):
    _, _, page = get(url)
    root = html.fromstring(page)
    movie_divs = root.xpath('//div[@class="item"]')
    movies = [movie_from_div(div) for div in movie_divs]
    return movies


def main():
    #豆瓣电影 top250
    for i in range(10):
        url = 'https://movie.douban.com/top250?start={}'.format(25 * i)
        movies = movies_from_url(url)
        for movie in movies:
            print(movie)


if __name__ == '__main__':
    main()