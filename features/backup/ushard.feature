Feature: ushard

	@test
	Scenario: add ushard group should succeed
	  When I found 2 valid ports, or I skip the test
	  And I add a Ushard group
	  Then the response is ok
	  And the Ushard group list should contains the Ushard group

	@test
	Scenario: add ushard m-s instances should succeed
	  When I found a Ushard group without Ushard instance, or I skip the test
	  And I found a server without ushard
	  And I add Ushard instance in the Ushard group
	  Then the response is ok
	  And the Ushard group should have 1 running Ushard instance in 11s

	  When I found a server without ushard
	  And I add Ushard instance in the Ushard group
	  Then the response is ok
	  And the Ushard group should have 2 running Ushard instance in 11s

#	@test @wip
#	Scenario: add data nodes to ushard group should succeed
#	  When I found 1 Ushard group with Ushard instance, or I skip the test
#	  And I found 2 MySQL groups with MySQL HA instances, or I skip the test
#	  And I configure the Ushard group by adding 2 users to the MySQL groups
#	  And I create test table to dble by user1
#	  And I create test table to dble by user2
#	  Then the response is ok
#	  When I insert data to dble by user1
#	  Then I found the data in MySQL by user1
#	  When I insert data to dble by user2
#	  Then I found the data in MySQL by user2

	@test
	Scenario: remove ushard should succeed
	  When I found a Ushard group without Ushard instance, or I skip the test
	  And I remove the Ushard group
	  Then the response is ok
	  And the Ushard group list should not contains the Ushard group

