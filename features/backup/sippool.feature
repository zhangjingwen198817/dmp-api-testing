Feature: sippool
	@test @case.272
	Scenario: sippool/add and sippool/remove should succeed
	  When I found a ip segments xx.xx.0.0/16 which not contains in sip pool
	  And I add ip xx.xx.1.2 to sip pool
	  Then the response is ok
	  And the sip pool should contain xx.xx.1.2

	  When I add ip xx.xx.1.3-xx.xx.1.5 to sip pool
	  Then the response is ok
	  And the sip pool should contain xx.xx.1.3,xx.xx.1.4,xx.xx.1.5

	  When I add ip xx.xx.1.6,xx.xx.1.8 to sip pool
	  Then the response is ok
	  And the sip pool should contain xx.xx.1.6,xx.xx.1.8

	  When I add ip xx.xx.1.9,xx.xx.1.10-xx.xx.1.20 to sip pool
	  Then the response is ok
	  And the sip pool should contain xx.xx.1.10,xx.xx.1.20
	  And the sip pool should have 18 ips match xx.xx.1.*

	  When I add ip xx.xx.2.0/24 to sip pool
	  Then the response is ok
	  And the sip pool should contain xx.xx.2.1,xx.xx.2.123,xx.xx.2.123
	  And the sip pool should have 254 ips match xx.xx.2.*

	  When I remove ip xx.xx.2.0/24 from sip pool
	  Then the response is ok
	  And the sip pool should not contain xx.xx.2.1,xx.xx.2.123,xx.xx.2.123
	  And the sip pool should have 0 ips match xx.xx.2.*

	  When I remove ip xx.xx.1.9,xx.xx.1.10-xx.xx.1.20 from sip pool
	  Then the response is ok
	  And the sip pool should not contain xx.xx.1.10,xx.xx.1.20

	  When I remove ip xx.xx.1.6,xx.xx.1.8 from sip pool
	  Then the response is ok
	  And the sip pool should not contain xx.xx.1.6,xx.xx.1.8

	  When I remove ip xx.xx.1.3-xx.xx.1.5 from sip pool
	  Then the response is ok
	  And the sip pool should not contain xx.xx.1.3,xx.xx.1.4,xx.xx.1.5
	  
	  When I remove ip xx.xx.1.2 from sip pool
	  Then the response is ok
	  And the sip pool should not contain xx.xx.1.2