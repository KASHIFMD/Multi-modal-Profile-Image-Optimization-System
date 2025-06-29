# Base image: CentOS Stream 9 from Quay.io
# FROM quay.io/centos/centos:stream9
FROM nvidia/cuda:12.0.0-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV DOCROOT="/opt/api"

# Set the working directory
WORKDIR ${DOCROOT}

# Install necessary packages and Python
RUN apt-get update && \
    apt-get install -y nano software-properties-common python3-pip tzdata git ffmpeg wget curl libgl1 libglib2.0-0 iputils-ping && \
    apt-get install -y nano software-properties-common python3-pip tzdata git ffmpeg wget curl libgl1 libglib2.0-0 && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    ln -fs /usr/share/zoneinfo/Asia/Kolkata /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file and install Python dependencies
COPY requirement.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install basicsr facexlib gfpgan && \
    pip install -r requirement.txt

# Fix the import issue dynamically based on Python version
RUN PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')") && \
    if [ -z "$PYTHON_VERSION" ]; then \
        echo "Python version not found"; \
    else \
        sed -i 's/from torchvision.transforms.functional_tensor import rgb_to_grayscale/from torchvision.transforms.functional import rgb_to_grayscale/' /usr/local/lib/python${PYTHON_VERSION}/dist-packages/basicsr/data/degradations.py; \
    fi

COPY . .

ENV PORT=5008
# Expose the application port
EXPOSE ${PORT}

# Start FastAPI with Uvicorn
CMD ["python3", "start.py"]
