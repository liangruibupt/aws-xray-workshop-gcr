# AWS X-Ray SDK for Java

## Instrument Code Change:

### 1. Add the X-Ray SDK for Java's tracing filter to your servlet configuration in a WebConfig class or web.xml file.

Servlet configuration

```java
import com.amazonaws.xray.AWSXRay;
import com.amazonaws.xray.AWSXRayRecorderBuilder;
import com.amazonaws.xray.plugins.EC2Plugin;
import com.amazonaws.xray.plugins.ElasticBeanstalkPlugin;
import com.amazonaws.xray.strategy.sampling.LocalizedSamplingStrategy;

@Configuration
public class WebConfig {
...
  static {
    AWSXRayRecorderBuilder builder = AWSXRayRecorderBuilder.standard().withPlugin(new EC2Plugin()).withPlugin(new ElasticBeanstalkPlugin());

    URL ruleFile = WebConfig.class.getResource("/sampling-rules.json");
    builder.withSamplingStrategy(new LocalizedSamplingStrategy(ruleFile));

    AWSXRay.setGlobalRecorder(builder.build());
  }
}
```

Tomcat ServletContextListener

```java
import com.amazonaws.xray.AWSXRay;
import com.amazonaws.xray.AWSXRayRecorderBuilder;
import com.amazonaws.xray.plugins.EC2Plugin;
import com.amazonaws.xray.strategy.sampling.LocalizedSamplingStrategy;

import java.net.URL;
import javax.servlet.ServletContextEvent;
import javax.servlet.ServletContextListener;

public class Startup implements ServletContextListener {

    @Override
    public void contextInitialized(ServletContextEvent event) {
        AWSXRayRecorderBuilder builder = AWSXRayRecorderBuilder.standard().withPlugin(new EC2Plugin());

        URL ruleFile = Startup.class.getResource("/sampling-rules.json");
        builder.withSamplingStrategy(new CentralizedSamplingStrategy(ruleFile));

        AWSXRay.setGlobalRecorder(builder.build());
    }

    @Override
    public void contextDestroyed(ServletContextEvent event) { }
}
```

[sampling-rules.json](script/sampling-rules.json)

WEB-INF/web.xml

```xml
<filter>
  <filter-name>AWSXRayServletFilter</filter-name>
  <filter-class>com.amazonaws.xray.javax.servlet.AWSXRayServletFilter</filter-class>
  <init-param>
    <param-name>dynamicNamingRecognizedHosts</param-name>
    <param-value>*.example.com</param-value>
  </init-param>
  <init-param>
    <param-name>dynamicNamingFallbackName</param-name>
    <param-value>MyApp</param-value>
  </init-param>
</filter>
<filter-mapping>
  <filter-name>AWSXRayServletFilter</filter-name>
  <url-pattern>*</url-pattern>
</filter-mapping>
```


### 2. Take the X-Ray SDK for Java's submodules as build dependencies in your Maven or Gradle build configuration.

- The [Example pom.xml dependencies for Maven](script/pom.xml)
- The [Example build.gradle - dependencies for Gradle](script/build.gradle)

### 3. Use the X-Ray SDK for Java to instrument your AWS SDK

Whenever you make a call to a downstream AWS service or resource with an instrumented client, tracing data will be collected. 

```java
import com.amazonaws.xray.AWSXRay;
import com.amazonaws.xray.handlers.TracingHandler;
public class MyModel {
  private AmazonDynamoDB client = AmazonDynamoDBClientBuilder.standard()
        .withRegion(Regions.fromName(System.getenv("AWS_REGION")))
        .withRequestHandlers(new TracingHandler(AWSXRay.getGlobalRecorder()))
        .build();
```

### 4. You can use the X-Ray SDK for Java versions of HTTPClient and HTTPClientBuilder to instrument Apache HTTP clients. To instrument SQL queries, add the SDK's interceptor to your data source. 

```java
....
import com.amazonaws.xray.proxies.apache.http.HttpClientBuilder;
...
  public String randomName() throws IOException {
    CloseableHttpClient httpclient = HttpClientBuilder.create().build();
    HttpGet httpGet = new HttpGet("http://names.example.com/api/");
    CloseableHttpResponse response = httpclient.execute(httpGet);
    ...
  }
```

```java
import org.apache.tomcat.jdbc.pool.DataSource;
...
DataSource source = new DataSource();
source.setUrl(url);
source.setDriverClassName("com.mysql.jdbc.Driver");
source.setJdbcInterceptors("com.amazonaws.xray.sql.mysql.TracingInterceptor;");
...
```

## Passing segment context between threads in a multithreaded application
```java
import com.amazonaws.xray.AWSXRay;
import com.amazonaws.xray.AWSXRayRecorder;
import com.amazonaws.xray.entities.Entity;
import com.amazonaws.xray.entities.Segment;
import com.amazonaws.xray.entities.Subsegment;
...
      Entity segment = recorder.getTraceEntity();
      Thread comm = new Thread() {
        public void run() {
          recorder.setTraceEntity(segment);
          Subsegment subsegment = AWSXRay.beginSubsegment("## Send notification");
          Sns.sendNotification("Scorekeep game completed", "Winner: " + userId);
          AWSXRay.endSubsegment();
        }
```

## Instrument Plugins
- Amazon EC2 – EC2Plugin adds the instance ID, Availability Zone, and the CloudWatch Logs Group.
- Elastic Beanstalk – ElasticBeanstalkPlugin adds the environment name, version label, and deployment ID.
- Amazon ECS – ECSPlugin adds the container ID.
- Amazon EKS – EKSPlugin adds the container ID, cluster name, pod ID, and the CloudWatch Logs Group.


## Logging
1. application.properties

logging.level.com.amazonaws.xray = DEBUG

2. Trace ID injection into logs for Log4J2 and Logback

PatternLayout With ID injection: `%d{HH:mm:ss.SSS} [%t] %X{AWS-XRAY-TRACE-ID} %-5p %m%n`

