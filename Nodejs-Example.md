# Nodejs Express Sample App Instrumented with AWS X-Ray Running on EC2

https://github.com/aws-samples/eb-node-express-sample/tree/xray

## code analysis
1. Add the SDK to your application's dependencies.
*package.json*
```json
"aws-xray-sdk" : "1.1.2"
```

2. Initialize the SDK client and add it to your application prior to declaring routes.

```javascript
// Include the AWS X-Ray Node.js SDK and set configuration
var XRay = require('aws-xray-sdk');
var AWS = XRay.captureAWS(require('aws-sdk'));
var http = XRay.captureHTTPs(require('http'));

// Configure
XRay.config([XRay.plugins.EC2Plugin, XRay.plugins.ElasticBeanstalkPlugin]);
XRay.middleware.setSamplingRules('sampling-rules.json');
XRay.middleware.enableDynamicNaming();
```
3. Use the SDK exceptions after declaring routes.

```javascript
// open segment
var app = express();
app.use(XRay.express.openSegment('myfrontend'));

// capture
app.get('/', function(req, res) {
        XRay.captureAsyncFunc('Page Render', function(seg) {
            res.render('index', {
                static_path: 'static',
                theme: process.env.THEME || 'flatly',
                flask_debug: process.env.FLASK_DEBUG || 'false'
            });
            seg.close();
        });
        
        res.status(200).end();
    });

// instument
app.post('/signup', function(req, res) {
        var seg = XRay.getSegment();
        seg.addAnnotation('email', req.body.email);
        seg.addAnnotation('theme', req.body.theme);
        seg.addAnnotation('previewAccess', req.body.previewAccess);

        // You logig
});

// close segment
app.use(XRay.express.closeSegment());
```

## Deploy the sample application via X-Ray console
1. Find the ElasticBeanstalkEnvironmentURL key. Copy the value into your web browser to visit the sample application.
2. Check to the service map.

![nodejs-sampleapp-servicemap](media/nodejs-sampleapp-servicemap.png)

3. Check the traces

![nodejs-sampleapp-traces](media/nodejs-sampleapp-traces.png)

4. Filter the traces

![nodejs-sampleapp-traces-filter](media/nodejs-sampleapp-traces-filter.png)

## Run the AWS X-Ray on EC2 linux
1. Install X-Ray daemon
```bash
#!/bin/bash
curl https://s3.dualstack.us-west-2.amazonaws.com/aws-xray-assets.us-west-2/xray-daemon/aws-xray-daemon-2.x.rpm -o /home/ec2-user/xray.rpm
sudo yum install -y /home/ec2-user/xray.rpm

tail -f /var/log/xray/xray.log
```

2. Open security group for 2000(TCP/UDP), 3306(TCP), 3000(TCP) ports

3. IAM permission for EC2 instance profile
- AWSXrayFullAccess
- AmazonS3FullAccess
- AmazonDynamoDBFullAccess
- AmazonRDSFullAccess

3. Create RDS MySQL

```bash
mysql -h <RDS_Endpoint> -P 3306 -u dbadmin -p
# Create a table
# Insert rows in table
```
Then populate mysql-config.json with the required information

4. Run the application

Note: NPM and Node 10+ installed

```bash
export AWS_DEFAULT_REGION=cn-northwest-1

git clone https://github.com/aws-samples/aws-xray-sdk-node-sample.git
cd aws-xray-sdk-node-sample
npm install
node index.js
```

5. access the EC2 or ALB
- Visit your web browser to visit the sample application.
    - Test a traced AWS SDK request
    - Test a traced HTTP request.
    - Test a traced MySQL query.
- Check to the service map.

![EC2-Nodejs-Servicemap](media/EC2-Nodejs-Servicemap.png)

You can also drill down the invocation error

![EC2-Nodejs-Error-Trace](media/EC2-Nodejs-Error-Trace.png)
