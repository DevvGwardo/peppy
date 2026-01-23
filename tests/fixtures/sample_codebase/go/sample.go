// Go sample code

package main

type User struct {
    Name string
    ID   int
}

type Service interface {
    GetUser(id int) (*User, error)
}

type UserService struct{}

func (s *UserService) GetUser(id int) (*User, error) {
    return &User{Name: "test", ID: id}, nil
}

func CalculateSum(a, b int) int {
    return a + b
}