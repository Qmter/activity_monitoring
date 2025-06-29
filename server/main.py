from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
import json
from datetime import datetime
import base64
import io

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Предупреждение: PIL не установлен. Некоторые функции могут быть недоступны.")

app = FastAPI(title="Система мониторинга")

class ClientStatus(BaseModel):
    computer_name: str
    user_name: str
    ip_address: str
    status: str
    last_activity: datetime

class ScreenshotRequest(BaseModel):
    computer_name: str
    image_data: str

class ScreenshotCommand(BaseModel):
    computer_name: str

clients = {}
screenshots_dir = "screenshots"
pending_screenshots = set()

os.makedirs(screenshots_dir, exist_ok=True)

@app.post("/client/status")
async def update_client_status(status: ClientStatus):
    clients[status.computer_name] = {
        "computer_name": status.computer_name,
        "user_name": status.user_name,
        "ip_address": status.ip_address,
        "status": status.status,
        "last_activity": status.last_activity.isoformat()
    }
    return {"message": "Status updated"}

@app.post("/client/screenshot")
async def receive_screenshot(screenshot: ScreenshotRequest):
    try:
        image_data = base64.b64decode(screenshot.image_data)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{screenshots_dir}/{screenshot.computer_name}_{timestamp}.png"
        
        with open(filename, "wb") as f:
            f.write(image_data)
        
        return {"message": "Screenshot saved", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/clients", response_model=List[dict])
async def get_clients():
    return list(clients.values())

@app.post("/api/request-screenshot")
async def request_screenshot(command: ScreenshotCommand):
    if command.computer_name not in clients:
        raise HTTPException(status_code=404, detail="Client not found")
    
    pending_screenshots.add(command.computer_name)
    return {"message": "Screenshot request sent"}

@app.get("/api/pending-screenshots")
async def get_pending_screenshots():
    return list(pending_screenshots)

@app.get("/api/screenshots/{computer_name}")
async def get_screenshots(computer_name: str):
    screenshots = []
    if os.path.exists(screenshots_dir):
        for filename in os.listdir(screenshots_dir):
            if filename.startswith(computer_name) and filename.endswith('.png'):
                filepath = os.path.join(screenshots_dir, filename)
                timestamp = os.path.getmtime(filepath)
                screenshots.append({
                    "filename": filename,
                    "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                    "url": f"/screenshots/{filename}"
                })
    
    return sorted(screenshots, key=lambda x: x["timestamp"], reverse=True)

@app.get("/screenshots/{filename}")
async def get_screenshot_file(filename: str):
    filepath = os.path.join(screenshots_dir, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    return FileResponse(filepath)

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Система мониторинга</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .client { background: white; border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .online { border-left: 4px solid #28a745; }
            .offline { border-left: 4px solid #dc3545; }
            .status { font-weight: bold; padding: 4px 8px; border-radius: 4px; }
            .online .status { background-color: #d4edda; color: #155724; }
            .offline .status { background-color: #f8d7da; color: #721c24; }
            .client-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
            .client-info { flex: 1; }
            .client-actions { display: flex; gap: 10px; }
            .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
            .btn-primary { background-color: #007bff; color: white; }
            .btn-primary:hover { background-color: #0056b3; }
            .btn-secondary { background-color: #6c757d; color: white; }
            .btn-secondary:hover { background-color: #545b62; }
            .screenshots { margin-top: 15px; }
            .screenshot-item { display: flex; justify-content: space-between; align-items: center; padding: 8px; background: #f8f9fa; border-radius: 4px; margin: 5px 0; }
            .screenshot-link { color: #007bff; text-decoration: none; }
            .screenshot-link:hover { text-decoration: underline; }
            .refresh-btn { background-color: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin-bottom: 20px; }
            .refresh-btn:hover { background-color: #218838; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Система мониторинга активности</h1>
                <button class="refresh-btn" onclick="loadClients()">Обновить</button>
            </div>
            <div id="clients"></div>
        </div>
        
        <script>
            async function loadClients() {
                try {
                    const response = await fetch('/api/clients');
                    const clients = await response.json();
                    
                    const container = document.getElementById('clients');
                    container.innerHTML = '';
                    
                    clients.forEach(client => {
                        const div = document.createElement('div');
                        div.className = `client ${client.status}`;
                        
                        const statusText = client.status === 'online' ? 'Онлайн' : 'Оффлайн';
                        
                        div.innerHTML = `
                            <div class="client-header">
                                <div class="client-info">
                                    <h3>${client.computer_name}</h3>
                                    <p><strong>Пользователь:</strong> ${client.user_name}</p>
                                    <p><strong>IP:</strong> ${client.ip_address}</p>
                                    <p><strong>Статус:</strong> <span class="status">${statusText}</span></p>
                                    <p><strong>Последняя активность:</strong> ${new Date(client.last_activity).toLocaleString()}</p>
                                </div>
                                <div class="client-actions">
                                    <button class="btn btn-primary" onclick="requestScreenshot('${client.computer_name}')">Скриншот</button>
                                    <button class="btn btn-secondary" onclick="loadScreenshots('${client.computer_name}', this)">История</button>
                                </div>
                            </div>
                            <div id="screenshots-${client.computer_name}" class="screenshots" style="display: none;"></div>
                        `;
                        container.appendChild(div);
                    });
                } catch (error) {
                    console.error('Ошибка загрузки клиентов:', error);
                }
            }
            
            async function requestScreenshot(computerName) {
                try {
                    const response = await fetch('/api/request-screenshot', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ computer_name: computerName })
                    });
                    
                    if (response.ok) {
                        alert('Запрос скриншота отправлен');
                    } else {
                        alert('Ошибка отправки запроса');
                    }
                } catch (error) {
                    console.error('Ошибка запроса скриншота:', error);
                    alert('Ошибка запроса скриншота');
                }
            }
            
            async function loadScreenshots(computerName, button) {
                const container = document.getElementById(`screenshots-${computerName}`);
                
                if (container.style.display === 'none') {
                    try {
                        const response = await fetch(`/api/screenshots/${computerName}`);
                        const screenshots = await response.json();
                        
                        if (screenshots.length === 0) {
                            container.innerHTML = '<p>Скриншоты не найдены</p>';
                        } else {
                            container.innerHTML = '<h4>История скриншотов:</h4>';
                            screenshots.forEach(screenshot => {
                                const item = document.createElement('div');
                                item.className = 'screenshot-item';
                                item.innerHTML = `
                                    <span>${new Date(screenshot.timestamp).toLocaleString()}</span>
                                    <a href="${screenshot.url}" target="_blank" class="screenshot-link">Просмотр</a>
                                `;
                                container.appendChild(item);
                            });
                        }
                        
                        container.style.display = 'block';
                        button.textContent = 'Скрыть';
                    } catch (error) {
                        console.error('Ошибка загрузки скриншотов:', error);
                        container.innerHTML = '<p>Ошибка загрузки скриншотов</p>';
                        container.style.display = 'block';
                    }
                } else {
                    container.style.display = 'none';
                    button.textContent = 'История';
                }
            }
            
            // Загружаем клиентов при загрузке страницы
            loadClients();
            
            // Обновляем каждые 30 секунд
            setInterval(loadClients, 30000);
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    print("Сервер мониторинга запускается...")
    if not PIL_AVAILABLE:
        print("Предупреждение: PIL не установлен. Функции обработки изображений недоступны.")
    uvicorn.run(app, port=8000) 