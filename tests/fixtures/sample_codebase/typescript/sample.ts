// TypeScript with interfaces and generics

interface IUser {
    id: number;
    name: string;
}

type Result<T> = Success<T> | Error;

interface Success<T> {
    status: 'success';
    data: T;
}

interface Error {
    status: 'error';
    message: string;
}

class ApiClient<T> {
    private baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    async get(url: string): Promise<Result<T>> {
        return { status: 'success', data: {} as T };
    }
}

function processData<T>(data: T): T {
    return data;
}