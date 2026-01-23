// Rust sample code

struct User {
    name: String,
    id: u32,
}

impl User {
    fn new(name: String, id: u32) -> Self {
        User { name, id }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

enum Status {
    Active,
    Inactive,
}

fn calculate_sum(a: i32, b: i32) -> i32 {
    a + b
}