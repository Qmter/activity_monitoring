#include <windows.h>
#include <string>
#include <thread>
#include <chrono>
#include <sstream>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <wininet.h>

#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "wininet.lib")

using namespace std;

class MonitorClient {
private:
    std::string serverUrl;
    std::string computerName;
    std::string userName;
    std::string ipAddress;
    bool isRunning;
public:
    MonitorClient() : isRunning(false) {
        char buffer[256];
        DWORD size = sizeof(buffer);
        GetComputerNameA(buffer, &size);
        computerName = std::string(buffer);
        size = sizeof(buffer);
        GetUserNameA(buffer, &size);
        userName = std::string(buffer);
        ipAddress = getLocalIP();
        serverUrl = "http://localhost:8000";
    }
    void start() {
        isRunning = true;
        sendStatus("online");
        while (isRunning) {
            checkScreenshotRequests();
            std::this_thread::sleep_for(std::chrono::seconds(10));
        }
    }
    void stop() {
        isRunning = false;
        sendStatus("offline");
    }
private:
    std::string getLocalIP() {
        WSADATA wsaData;
        if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) return "unknown";
        char hostname[256];
        if (gethostname(hostname, sizeof(hostname)) == 0) {
            struct addrinfo hints, *result;
            ZeroMemory(&hints, sizeof(hints));
            hints.ai_family = AF_INET;
            hints.ai_socktype = SOCK_STREAM;
            if (getaddrinfo(hostname, NULL, &hints, &result) == 0) {
                for (struct addrinfo* ptr = result; ptr != NULL; ptr = ptr->ai_next) {
                    if (ptr->ai_family == AF_INET) {
                        struct sockaddr_in* sockaddr_ipv4 = (struct sockaddr_in*)ptr->ai_addr;
                        char ip[INET_ADDRSTRLEN];
                        inet_ntop(AF_INET, &(sockaddr_ipv4->sin_addr), ip, INET_ADDRSTRLEN);
                        freeaddrinfo(result);
                        WSACleanup();
                        return std::string(ip);
                    }
                }
                freeaddrinfo(result);
            }
        }
        WSACleanup();
        return "unknown";
    }
    void sendStatus(const std::string& status) {
        std::string json = "{";
        json += "\"computer_name\":\"" + computerName + "\",";
        json += "\"user_name\":\"" + userName + "\",";
        json += "\"ip_address\":\"" + ipAddress + "\",";
        json += "\"status\":\"" + status + "\",";
        json += "\"last_activity\":\"" + getCurrentTime() + "\"";
        json += "}";
        std::string response;
        sendHttpPost("/client/status", json, response);
    }
    void checkScreenshotRequests() {
        std::string response;
        if (sendHttpGet("/api/pending-screenshots", response)) {
            if (response.find(computerName) != std::string::npos) {
                takeScreenshot();
            }
        }
    }
    void takeScreenshot() {
        std::string json = "{";
        json += "\"computer_name\":\"" + computerName + "\",";
        json += "\"image_data\":\"\"";
        json += "}";
        std::string response;
        sendHttpPost("/client/screenshot", json, response);
    }
    std::string getCurrentTime() {
        auto now = std::chrono::system_clock::now();
        auto time_t = std::chrono::system_clock::to_time_t(now);
        std::stringstream ss;
        tm buf;
        localtime_s(&buf, &time_t);
        ss << std::put_time(&buf, "%Y-%m-%dT%H:%M:%S");
        return ss.str();
    }
    bool sendHttpPost(const std::string& endpoint, const std::string& data, std::string& response) {
        std::string fullUrl = serverUrl + endpoint;
        HINTERNET hInternet = InternetOpenA("MonitorClient/1.0", INTERNET_OPEN_TYPE_DIRECT, NULL, NULL, 0);
        if (!hInternet) return false;
        URL_COMPONENTSA urlComp;
        ZeroMemory(&urlComp, sizeof(urlComp));
        urlComp.dwStructSize = sizeof(urlComp);
        urlComp.dwSchemeLength = -1;
        urlComp.dwHostNameLength = -1;
        urlComp.dwUrlPathLength = -1;
        if (!InternetCrackUrlA(fullUrl.c_str(), fullUrl.length(), 0, &urlComp)) {
            InternetCloseHandle(hInternet);
            return false;
        }
        HINTERNET hConnect = InternetConnectA(hInternet, (LPCSTR)urlComp.lpszHostName, urlComp.nPort, NULL, NULL, INTERNET_SERVICE_HTTP, 0, 0);
        if (!hConnect) {
            InternetCloseHandle(hInternet);
            return false;
        }
        HINTERNET hRequest = HttpOpenRequestA(hConnect, "POST", (LPCSTR)urlComp.lpszUrlPath, NULL, NULL, NULL, INTERNET_FLAG_RELOAD, 0);
        if (!hRequest) {
            InternetCloseHandle(hConnect);
            InternetCloseHandle(hInternet);
            return false;
        }
        std::string headers = "Content-Type: application/json\r\n";
        headers += "Content-Length: " + std::to_string(data.length()) + "\r\n";
        BOOL result = HttpSendRequestA(hRequest, headers.c_str(), headers.length(), (LPVOID)data.c_str(), data.length());
        if (result) {
            char buffer[1024];
            DWORD bytesRead;
            std::stringstream responseStream;
            while (InternetReadFile(hRequest, buffer, sizeof(buffer) - 1, &bytesRead) && bytesRead > 0) {
                buffer[bytesRead] = '\0';
                responseStream << buffer;
            }
            response = responseStream.str();
        }
        InternetCloseHandle(hRequest);
        InternetCloseHandle(hConnect);
        InternetCloseHandle(hInternet);
        return result == TRUE;
    }
    bool sendHttpGet(const std::string& endpoint, std::string& response) {
        std::string fullUrl = serverUrl + endpoint;
        HINTERNET hInternet = InternetOpenA("MonitorClient/1.0", INTERNET_OPEN_TYPE_DIRECT, NULL, NULL, 0);
        if (!hInternet) return false;
        HINTERNET hConnect = InternetOpenUrlA(hInternet, fullUrl.c_str(), NULL, 0, INTERNET_FLAG_RELOAD, 0);
        if (!hConnect) {
            InternetCloseHandle(hInternet);
            return false;
        }
        char buffer[1024];
        DWORD bytesRead;
        std::stringstream responseStream;
        while (InternetReadFile(hConnect, buffer, sizeof(buffer) - 1, &bytesRead) && bytesRead > 0) {
            buffer[bytesRead] = '\0';
            responseStream << buffer;
        }
        response = responseStream.str();
        InternetCloseHandle(hConnect);
        InternetCloseHandle(hInternet);
        return true;
    }
};

int main() {
    MonitorClient client;
    client.start();
    return 0;
} 