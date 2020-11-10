Feature: no scene restrictions test cases

  @case.1170 @version.09
  Scenario: single instance
    Given I found a random instance without repl_ip
    When I stop ha and replication for the instance in 1 concurrency
    Then the uguard_status of the instance should be disable
    And the mysql_instance_replication_status of the instance should be disable
    When I start ha for the instance in 1 concurrency
    Then the uguard_status of the instance should be OK
    When I rebuild replication for the instance in 1 concurrency
    Then the mysql_instance_replication_status of the instance should be OK

  @case.1171 @version.09
  Scenario: three groups of instances without repl_ip
    Given I found 3 groups in group_B without repl_ip
    When I stop ha and replication for the instance in 3 concurrency
    Then the uguard_status of the instance should be disable
    And the mysql_instance_replication_status of the instance should be disable
    When I start ha for the instance in 3 concurrency
    Then the uguard_status of the instance should be OK
    When I rebuild replication for the instance in 3 concurrency
    Then the mysql_instance_replication_status of the instance should be OK

    When I stop ha for the instance in 3 concurrency
    Then the uguard_status of the instance should be disable
    When I start ha for the instance in 3 concurrency
    Then the uguard_status of the instance should be OK

    When I found one of the instances and stop ha
    And I stop ha for the instance in 3 concurrency
    Then the uguard_status of the instance should be disable
    When I found one of the instances and start ha
    And I start ha for the instance in 3 concurrency
    Then the uguard_status of the instance should be OK

  @case.1173 @version.09
  Scenario: two groups of instances with repl_ip
    Given I found 2 groups in group_B with repl_ip
    When I stop ha and replication for the instance in 2 concurrency
    Then the uguard_status of the instance should be disable
    And the mysql_instance_replication_status of the instance should be disable
    When I start ha for the instance in 2 concurrency
    Then the uguard_status of the instance should be OK
    When I rebuild replication for the instance in 2 concurrency
    Then the mysql_instance_replication_status of the instance should be OK

  @case.1174 @version.09
  Scenario: a group in group_C
    When I found 1m4s-C1 MySQL group with 5 MySQL instances,or I skip the test
    Given I got the slave instances in the group
    When I stop ha and replication for the instance in 1 concurrency
    Then the uguard_status of the instance should be disable
    And the mysql_instance_replication_status of the instance should be disable
    When I start ha for the instance in 1 concurrency
    Then the uguard_status of the instance should be OK
    When I rebuild replication for the instance in 1 concurrency
    Then the mysql_instance_replication_status of the instance should be OK

  @case.1175 @version.09
  Scenario: manual trigger exercise task
    When I trigger the uguard exercise task by the way manual
    Then the exercise result should be success

  @case.1176 @version.09
  Scenario: auto trigger exercise task
    When I stop all the uguard manager
    And I update the uguard exercise task config
    Then the exercise task should config correct
    And the exercise task should be running
    And the result of the exercise task should be timeout
    When I start all the uguard manager
    Then the exercise result should be success

  @case.1006 @version.09
  Scenario: 1006-add a tag to a server
    When I create a tag in tag pool with attribute server
    Then the response is ok
    And the tag should be in the tag pool
    When I found a server and add the tag
    Then the response is ok
    And the tag should be in the server tag list

  @case.1007-1  @version.09
  Scenario: 1007-1-silence a server
    When I found a dmp server
    And I silent the server
    Then the response is ok
    And the server should in the silence list

  @case.1007-2  @version.09
  Scenario: 1007-2-resume a server from silence
    When I found a server in silence
    And I resume the server from silence
    Then the response is ok
    And the server should not in the silence list

  @case.1008 @version.09
  Scenario: 1008-add ip to sip pool/remove ip from sip pool
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

  @case.1009_1 @version.09
  Scenario Outline: 1009_1-add an Highly Available policy template
    When I add a <type> template, in version 4
    Then the response is ok
    And the Highly Available policy list should contains the <type> template

    Examples: sla type
      | type        |
      | rto         |
      | rpo         |
      | ha_policy   |
      | ha_policy_1 |

  @case.1009_2 @version.09
  Scenario Outline: 1009_2-update an Highly Available policy template
    When I found a valid <type> template, or I skip the test
    And I update the <type> template, with the configuration <config>
    Then the response is ok
    Then the <type> template should be configuration <config>

    Examples: sla config
      | type        | config                              |
      | rto         | rto-400                             |
      | rpo         | rpo-500                             |
      | ha_policy   | number_semi-synchronous_instances_1 |
      | ha_policy_1 | number_semi-synchronous_instances   |

  @case.1009_3 @version.09
  Scenario Outline: 1009_3-remove an Highly Available policy template
    When I found a valid <type> template, or I skip the test
    And I remove the <type> template
    Then the response is ok
    And the <type> template should not exist

    Examples: sla type
      | type        |
      | rto         |
      | rpo         |
      | ha_policy   |
      | ha_policy_1 |

  @case.1101  @version.09
  Scenario: 1101-silence a instance
    When I found a MySQL instance
    And I silent the instance
    Then the response is ok
    And the instance should in the silence list

  @case.1103  @version.09
  Scenario: 1103-resume a instance from silence
    When I found a MySQL instance in silence
    And I resume the instance from silence
    Then the response is ok
    And the instance should not in the silence list

  @case.1105  @version.09
  Scenario: 1105-check the detail of the backup set
    When I found a backup set, or I skip the test
    And I check the detail of the backup set
    Then the detail of the backup set should be viewed

  @case.1106  @version.09
  Scenario: 1106-delete the backup set
    When I make a manual backup with Xtrabackup in instance
    Then the MySQL instance manual backup list should contains the urman backup set in 1m
    When I delete the backup set
    Then got the response successful in 60s
    And the backup set should not in the backup set list

  @case.1130 @version.09
  Scenario: 1130-Udb is hidden
    When I show udb
    Then the response is ok
    Then the MySQL group list should contains the MySQL group
    Then the MySQL instance should be in the MySQL instance list

    When I hide udb
    Then the response is ok
    Then the MySQL group list should not contains the MySQL group
    Then the MySQL instance should not be in the MySQL instance list

  @case.1135-1  @version.09
  Scenario: 1135-1-add a tag to the group
    When I create a tag in tag pool with attribute group
    Then the response is ok
    And the tag should be in the tag pool
    When I found a MySQL group,or I skip the test
    And I add a tag to the group
    Then the response is ok
    And the tag should be in the group tag list

  @case.1135-2  @version.09
  Scenario: 1135-2-remove the tag from the group
    When I found a group with tag attributed group
    And I remove the tag from the group
    Then the response is ok
    And the tag should not be in the group tag list


  @case.1139 @version.09
  Scenario Outline: Umc Authority user
    When I create <role> with administrator authorities,or I skip the test if the role already exists
    Then the response is ok
    Then the role list should contain the role
    Then the <role> should contain <authority>

    When I create <user> with the role,password is <password>,or I skip the test if the user already exists
    Then the response is ok
    Then the user list should contain the user

    When I logout of the current user
    And I login with <user>,<password>
    Then the login user should be <user>

    When I add a MySQL group
    Then the response is ok
    Then the MySQL group list should contains the MySQL group

    When I logout of the current user
    And I login with admin,admin
    Then the login user should be admin

    When I update <role> without <authority>,or I skip the test if the role already exists
    Then the response is ok
    Then the <role> should not contain <authority>

    When I logout of the current user
    And I login with <user>,<password>
    Then the login user should be <user>

    When I add a MySQL group
    Then the response is not ok
    Then the MySQL group list should not contains the MySQL group

    When I logout of the current user
    And I login with admin,admin
    Then the login user should be admin
    Examples:
      | role   | user   | password | authority          |
      | role01 | user01 | 123456   | add-database-group |

  @case.1123 @version.09
  Scenario: 1123&1124-add and remove alert channel
    When I remove all the alert_channel
    Then the response is ok
    And the alert channel list should not contains the alert channel
    When I add an alert channel for smtp
    Then the response is ok
    And the alert channel list should contains the smtp alert channel
    When I remove all the alert_channel
    Then the response is ok
    And the alert channel list should not contains the smtp alert channel
    When I add an alert channel for wechat
    Then the response is ok
    And the alert channel list should contains the wechat alert channel
    When I remove all the alert_channel
    Then the response is ok
    And the alert channel list should not contains the wechat alert channel

  @inhibit @case.1125 @version.09
  Scenario: 1125-add inhibit rule
    When I remove all the inhibit_rule
    Then the response is ok
    And the inhibit rule list should not contains the new inhibit rule
    When I add a inhibit rule
    Then the response is ok
    And the inhibit rule list should contains the new inhibit rule

  @inhibit @case.1126 @version.09
  Scenario: 1126-remove inhibit rule
    When I found a new inhibit rule in the inhibit rule list
    And I remove all the inhibit_rule
    Then the response is ok
    And the inhibit rule list should not contains the new inhibit rule

  @case.1128 @version.09
  Scenario: 1128-mark a unresolved alert to resolved
    When I creat an test unresolved alert in 1m
    Then the response is ok
    And the test unresolved alert should in the unresolved alert list
    When I mark the unresolved alert to resolved in 1m
    Then the response is ok
    And the test unresolved alert should not in the unresolved alert list

  @case.1129 @version.09
  Scenario: 1129-create and remove silence rule
    When I create a silence rule
    Then the response is ok
    And the silence rule should in the silence rule list
    When I remove the silence rule
    Then the response is ok
    And the silence rule should not in the silence rule list

#  @case.1152
#  Scenario: 1152-download logs from server
#    When I add a server
#    Then the response is ok
#    And the server should be in the server list
#    When I download logs from the server
#    Then I should download the correct files
#    When I remove a server
#    Then the response is ok
#    And the server should not be in the server list

#  @case.1153
#  Scenario: 1153-get system message log and error log
#    When I found a MySQL instance
#    And I found the server which the instance running on
#    And I get the system message log
#    Then the log is not empty
#    When I get the MySQL error log
#    Then the log is not empty
	
  @case.1167
  Scenario: batch install in one group
    When I found all server with components uguard-agent,urman-agent,ustats,udeploy, or I skip the test
    And I batch install in one group MySQL instances
    Then the batch MySQL group should have 1 running MySQL master and 2 running MySQL slave in 60s