# escape=`

ARG BASE_IMAGE_TAG="ltsc2022"
FROM mcr.microsoft.com/windows/server:${BASE_IMAGE_TAG}

SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]

RUN New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
	-Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

ARG BASE_IMAGE_TAG
ARG WINGET_VERSION

# OCI labels for metadata
LABEL org.opencontainers.image.title="Windows Server Image with winget CLI"
LABEL org.opencontainers.image.description="Windows Server Image with winget CLI"
LABEL org.opencontainers.image.version="${WINGET_VERSION}-${BASE_IMAGE_TAG}"
LABEL org.opencontainers.image.url="https://github.com/s-weigand/winget-docker"
LABEL org.opencontainers.image.documentation="https://github.com/s-weigand/winget-docker/blob/main/README.md"
LABEL org.opencontainers.image.source=https://github.com/s-weigand/winget-docker

RUN $vcRedistUrl='https://aka.ms/vs/17/release/vc_redist.x64.exe'; `
    $installerPath='C:\vc_redist.x64.exe'; `
    (New-Object System.Net.WebClient).DownloadFile($vcRedistUrl, $installerPath); `
    Start-Process -FilePath $installerPath -ArgumentList '/install', '/quiet', '/norestart' -NoNewWindow -Wait; `
    Remove-Item -Path $installerPath -Force

COPY ./winget_min_cli C:/winget-cli

RUN [Environment]::SetEnvironmentVariable('PATH', [Environment]::GetEnvironmentVariable('PATH') + ';C:/winget-cli', 'Machine')

