# 启动后端
Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload" -WorkingDirectory ".\backend" -WindowStyle Minimized

# 启动前端
Start-Process -FilePath "npx.cmd" -ArgumentList "vite", "--host", "0.0.0.0", "--port", "5173" -WorkingDirectory ".\frontend" -WindowStyle Minimized

Write-Host "服务已启动:" -ForegroundColor Green
Write-Host "  前端: http://localhost:5173" -ForegroundColor Cyan
Write-Host "  后端: http://localhost:8000" -ForegroundColor Cyan
