{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "s3:GetObjectVersionTagging",
                "s3:GetObjectAcl",
                "s3:GetBucketObjectLockConfiguration",
                "s3:GetIntelligentTieringConfiguration",
                "s3:GetObjectVersionAcl",
                "s3:GetBucketPolicyStatus",
                "s3:GetObjectRetention",
                "s3:GetBucketWebsite",
                "s3:GetObjectAttributes",
                "s3:GetObjectLegalHold",
                "s3:GetBucketNotification",
                "s3:GetReplicationConfiguration",
                "s3:ListMultipartUploadParts",
                "s3:GetObject",
                "s3:GetAnalyticsConfiguration",
                "s3:GetObjectVersionForReplication",
                "s3:GetLifecycleConfiguration",
                "s3:GetBucketTagging",
                "s3:GetInventoryConfiguration",
                "s3:ListBucketVersions",
                "s3:GetBucketLogging",
                "s3:ListBucket",
                "s3:GetAccelerateConfiguration",
                "s3:GetObjectVersionAttributes",
                "s3:GetBucketPolicy",
                "s3:GetObjectVersionTorrent",
                "s3:GetEncryptionConfiguration",
                "s3:GetBucketRequestPayment",
                "s3:GetObjectTagging",
                "s3:GetMetricsConfiguration",
                "s3:GetBucketOwnershipControls",
                "s3:GetBucketPublicAccessBlock",
                "s3:ListBucketMultipartUploads",
                "s3:GetBucketVersioning",
                "s3:GetBucketAcl",
                "s3:GetObjectTorrent"
            ],
            "Resource": [
                "arn:aws:s3:::${s3_cloudtrail_name}/*",
                "arn:aws:s3:::${s3_cloudtrail_name}"
            ]
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": [
                "arn:aws:s3:::${s3_lambda_outputs}/*",
                "arn:aws:s3:::${s3_lambda_outputs}"
            ]
        },
        {
            "Sid": "VisualEditor11111",
            "Effect": "Allow",
            "Action": [
                "sso-directory:*",
                "identitystore:*",
                "identitystore-auth:*",
                "sso:ListDirectoryAssociations"
            ],
            "Resource": [
                "arn:aws:identitystore::${account_id}:identitystore/${identitystore_id}",
                "arn:aws:sso:::instance/${sso_instance_id}",
                "arn:aws:identitystore:::group/*",
                "arn:aws:identitystore:::user/*",
                "arn:aws:identitystore:::membership/*"
            ]
        },
        {
            "Sid": "VisualEditor111",
            "Effect": "Allow",
            "Action": "lambda:InvokeFunction",
            "Resource": "arn:aws:lambda:eu-west-2:${account_id}:function:asdu-*"
        },
        {
            "Sid": "VisualEditor1111",
            "Effect": "Allow",
            "Action": "iam:ListUsers",
            "Resource": "arn:aws:iam::${account_id}:user/"
        }
    ]
}