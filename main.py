import socket
import threading
import time
import os
import sys 
import configparser 
import shutil

maximum_connect = 30
valid_method = ['GET', 'POST', 'HEAD', '--HEAD']
proxy_host = '127.0.0.1'
proxy_port = 8888
server_port = 80
main_directory = "Cache"
time_limit_page = "time-limit.html"
error_page = "403-error.html"
time_css = "time-limit.css"
error_css = "403-error.css"

def create_or_clear_directory(directory_name):
    if os.path.exists(directory_name):
        for item in os.listdir(directory_name):
            item_path = os.path.join(directory_name, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
    else:
        os.makedirs(directory_name)

def get_image_from_cache(cache_directory, website, image_name):
    file_path = os.path.join(cache_directory, website, image_name)
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return f.read()
    else:
        print("Lấy dữ liệu từ cache không thành công!")
        return None


def put_image_in_cache(cache_directory, website, image_name, image_data):
    website_directory = os.path.join(cache_directory, website)
    if not os.path.exists(website_directory):
        os.makedirs(website_directory)
    file_path = os.path.join(website_directory, image_name)
    with open(file_path, "wb") as f:
        f.write(image_data)

def initialize_cache(cache_timeout, cache_directory):
    current_time = time.time()
    for folder in os.listdir(cache_directory):
        folder_path = os.path.join(cache_directory, folder)

        if os.path.isdir(folder_path):
            folder_create_time = os.path.getctime(folder_path)
            if current_time - folder_create_time >= cache_timeout:
                shutil.rmtree(folder_path)
                print(f"Đã xóa thư mục '{folder}' vì đã vượt quá thời gian timeout.")

def read_config_file(file_name):
    config = configparser.ConfigParser()
    config.read(file_name)
    cache_time = int(config.get('CONFIG', 'cache_time'))
    whitelist = config.get('CONFIG', 'whitelisting').split(',')
    start_time, end_time = map(int, config.get('CONFIG', 'time').split('-'))
    return cache_time, whitelist, start_time, end_time

def time_access_allowed(start_time, end_time):
    current_hour = time.localtime().tm_hour 
    if start_time <= current_hour <= end_time:
        return True
    else:
        return False

def resolve_domain_to_ip(domain): #example.com/login
    if domain.startswith("www."):
        domain = domain[4:]
    try:
        ip_address = socket.gethostbyname(domain)
        return ip_address
    except socket.gaierror:
        return None

def read_html_and_css(html_file, css_file):
    try:
        with open(html_file, 'r', encoding='utf-8') as html:
            html_content = html.read()

        with open(css_file, 'r', encoding='utf-8') as css:
            css_content = css.read()

        combined_content = f"{html_content}\n<style>{css_content}</style>"

        return combined_content

    except Exception as e:
        print("Error:", e)
        return None

def analyze_header(request_data):
    data = request_data.split(b"\r\n\r\n")
    lines = data[0].split(b"\r\n")
    if len(lines) < 1:
        return None, None, None
    method, domain, _ = lines[0].split(b" ", 2)
    info_dict = {}
    for line in lines[1:]:
        if b":" in line:
            key, value = line.split(b":", 1)
            header_type = key.strip().lower().decode("utf-8")
            header_data = value.strip().lower().decode("utf-8")
            info_dict[header_type] = header_data
    return method.decode("utf-8"), domain.decode("utf-8"), info_dict

def respone_from_server(client_socket):
    cache_time, white_list, start_time, end_time = read_config_file("config.ini")
    request = client_socket.recv(4096)
    if request:
        method, domain, info_dict = analyze_header(request)
        image = domain.split("/")[-1]
        domain = domain.split("//")[-1]
        domain = domain.split("/")[0]
        if domain in white_list:
            if time_access_allowed(start_time, end_time):
                ip_server = resolve_domain_to_ip(domain)
                if ip_server:
                    if method.upper() in valid_method:
                        if "image/" in info_dict.get("accept", "") and len(image) > 0:
                            cache = get_image_from_cache(main_directory, domain, image)
                            if cache:
                                print("Lấy thông tin từ cache thành công!")
                                client_socket.sendall(cache)
                                client_socket.close()
                                return
                        try:
                            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            server_socket.connect((ip_server,server_port))
                            print(f"Kết nối tới trang web {domain}.")
                            server_socket.sendall(request)
                            response = b""
                            while b"\r\n\r\n" not in response:
                                data = server_socket.recv(999999)
                                response += data
                            if method.upper() == "HEAD":
                                client_socket.sendall(response)
                                client_socket.close()
                                server_socket.close()
                                return
                            if method.upper() == "POST" and b"100" in response.split(b"\r\n")[0]:
                                server_socket.sendall(response)
                                data = server_socket.recv(999999)
                                response = data
                            thing1, thing2, info_dict = analyze_header(response)
                            if "transfer-encoding" in info_dict:
                                while not response.endswith(b"0\r\n\r\n"):
                                    try:
                                        data = server_socket.recv(999999)
                                        response += data 
                                    except Exception as e:
                                        print(f"Xảy ra lỗi khi cố gắng lấy thông tin từ máy chủ {domain}: {e}")
                                        break
                            elif "content-length" in info_dict:
                                while len(response) < int(info_dict["content-length"]):
                                    try:
                                        data = server_socket.recv(999999)
                                        response += data 
                                    except Exception as e:
                                        print(f"Xảy ra lỗi khi cố gắng lấy thông tin từ máy chủ {domain}: {e}")
                                        break
                            if info_dict.get("content-type", "").startswith("image/"):
                                head, body = response.split(b"\r\n\r\n", 1)
                                put_image_in_cache(main_directory,domain, image, body)
                            client_socket.sendall(response)
                            print(f"Nhận dữ liệu từ {domain} thành công!")
                        except socket.error as e:
                            print("Lỗi kết nối: ", e)
                        finally:
                            server_socket.close()
                    else: #wrong method
                        print(f"Phương thức {method.upper()} không hợp lệ!")
                        client_socket.send(read_html_and_css(error_page, error_css).encode("utf-8"))
                else: # ip khong ton tai
                    print("Không thể phân giải tên miền thành IP!")
                    client_socket.send(read_html_and_css(error_page, error_css).encode("utf-8"))
            else: # time limit
                print("Truy cập bị giới hạn thời gian!")
                client_socket.send(read_html_and_css(time_limit_page, time_css).encode("utf-8"))
        else: # khong ton tai trong white list
            print(f"Tên miền {domain} không nằm trong danh sách được phép truy cập!")
            client_socket.send(read_html_and_css(error_page, error_css).encode("utf-8"))
    else: # request khong ton tai
        print("Yêu cầu của client không tồn tại!")
        client_socket.send(read_html_and_css(error_page, error_css).encode("utf-8"))
    client_socket.close()

def main():
    cache_time, white_list, start_time, end_time = read_config_file("config.ini")
    create_or_clear_directory(main_directory)
    proxy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_server.bind((proxy_host, proxy_port))
    proxy_server.listen(maximum_connect)
    print(f"Máy chủ proxy chạy trên địa chỉ: {proxy_host}, cổng: {proxy_port}")
    while True:
        initialize_cache(cache_time, main_directory)
        try:
            client_socket, client_addr = proxy_server.accept()
            print(f"Phát hiện một kết nối mới: {client_addr}")
            threading.Thread(target=respone_from_server, args=(client_socket,)).start()
        except Exception as e:
            print("Lỗi kết nối: ", e)
            print(f"Có lỗi xuất hiện khi cố gắng kết nối với client!")
            continue
    proxy_server.close()

if __name__ == "__main__":
    main()
