
FROM public.ecr.aws/lambda/python:3.8

# Install dependencies
RUN yum -y install \
    unzip \
    libX11 \
    mesa-libGL \
    mesa-libEGL \
    libXScrnSaver \
    alsa-lib \
    atk \
    cups-libs \
    gtk3 \
    libXcomposite \
    libXcursor \
    libXi \
    libXtst \
    pango \
    xorg-x11-fonts-Type1 \
    xorg-x11-fonts-misc

# Install chromedriver and google-chrome
RUN curl -O https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm && \
    yum -y localinstall google-chrome-stable_current_x86_64.rpm && \
    rm google-chrome-stable_current_x86_64.rpm

RUN curl -O https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/bin/chromedriver && \
    rm chromedriver_linux64.zip

# Copy function code
COPY izettleminbal.py ${LAMBDA_TASK_ROOT}

# Install Python dependencies
RUN pip install selenium boto3

CMD ["izettleminbal.lambda_handler"]