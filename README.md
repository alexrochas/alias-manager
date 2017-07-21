# Alias Manager
> CLI tool for managing terminal aliases

## Usage proposal

```gherkin
Feature: 
  As a linux user
  I want to be able to easily add and remove aliases
  In order to automatize my ambient
  
Scenario: Adding new alias
  Given a terminal
  When I type alias-manager new bc 'bundle exec'
  Then I should be able to use bc
  
Scenario: List alias
  Given a terminal
  And I already have the alias bc
  When I type alias-manager list
  Then I should be able to see bc
  
Scenario: Remove alias
  Given a terminal
  And I already have the alias bc
  When I type alias-manager remove bc
  Then I should not be able to use bc
```

```gherkin
Feature: 
  As a linux user
  I want to easily install my custom tools
  In order to automatize my ambient
  
Scenario: Installing alias-manager
  Given a terminal
  And I am using zsh
  When I install alias-manager
  Then I will be able to use alias-manager from the terminal
```

## Roadmap
  * Add basic functionality
  * Add per context aliases
  * Add basher support

## Meta

Alex Rocha - [about.me](http://about.me/alex.rochas)
