Renew the grid certificate used in Monet
----------------------------------------

When the grid certificate is close to the expiration time, obtain a 
`new grid robot certificate <https://ca.cern.ch/ca/user/Request.aspx?template=EE2Robot>`_ using the
``lbmonet`` service account. Download the certificate as ``MonetRobotCertificate.p12``.

Convert the certificate for grid usage (on ``lxplus`` for example)::

    openssl pkcs12 -in MonetRobotCertificate.p12 -out MonetRobotCertificate.pem -nokeys
    openssl pkcs12 -on MonetRobotCertificate.p12 -out MonetRobotKey.pem -nodes -nocerts

Use these files to :ref:`deploy monet<Deploy Monet on the online cluster>`.

