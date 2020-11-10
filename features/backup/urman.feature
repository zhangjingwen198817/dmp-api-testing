Feature: urman

  @test @case.272
	Scenario: urman_rule/remove_backup_rule should succeed
	  When I found a backup rule, or I skip the test
	  And I found the MySQL instance of the backup rule
	  And I remove the backup rule
	  Then the response is ok
	  And the backup rule should not exist
	  When I recycle the backup dir of the MySQL instance
	  Then the response is ok
	  And the backup dir of the MySQL instance should not exist

	@test @case.272 @slow
	Scenario: urman_rule/add_backup_rule should succeed
	  When I found a MySQL instance without backup rule, or I skip the test
	  And I add a backup rule to the MySQL instance, which will be triggered in 2m
	  Then the response is ok
	  And the MySQL instance should have a backup rule
	  And the MySQL instance should have a new backup set in 3m

	@test @case.272 @slow
	Scenario: urman_rule/update_backup_rule should succeed
	  When I found a backup rule, or I skip the test
	  And I found the MySQL instance of the backup rule
	  And I update the backup rule, make it will be triggered in 2m
	  Then the response is ok
	  And the MySQL instance should have a new backup set in 3m

    @test @case.272
    Scenario: database/manual backup instance should succeed
      When I found a running MySQL instance, or I skip the test
      And I make a manual backup on the MySQL instance
      Then the response is ok
      And the MySQL group manual backup list should contains the urman backup set in 2m