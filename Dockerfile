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

# Install Python dependencies
RUN pip uninstall -y urllib3
RUN pip install selenium -t ${LAMBDA_TASK_ROOT}
RUN pip install boto3 -t ${LAMBDA_TASK_ROOT}
RUN pip install websocket-client -t ${LAMBDA_TASK_ROOT}
RUN pip install urllib3==1.26.15 --ignore-installed -t ${LAMBDA_TASK_ROOT}
RUN pip install chromedriver -t ${LAMBDA_TASK_ROOT}

# Copy function code
COPY izettleminbal.py ${LAMBDA_TASK_ROOT}

CMD ["izettleminbal.lambda_handler"]