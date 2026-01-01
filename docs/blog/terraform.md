[introduction-terraform](https://lonegunmanb.github.io/introduction-terraform)

---

- 使用choco安装 [admin权限]
  - `choco install terraform`
  - `choco install consul` -> 启动 `consul agent -dev` -> 页面 http://localhost:8500

- 概念
  - terraform 是一个可以IaC [Infrastructure as code]工具，可以快速管理资源
    - 使用不同的provider操作不同的资源，如aws[aws]，oss[alicloud]，cos[tencentcloud]，docker[docker]
      - provider 查询地址 https://registry.terraform.io/browse/providers
      - 需要做什么资源的crud，则需要在代码中声明相应的provider，并在执行 init 后下载成功后方可运行[下载后provider是一个exe文件]。
      - 不同provider的 resource 定义不一样，可以查找相应的文档来看属性值怎么填写
      - data 和 resource 的区别
        - data用于查询已经存在资源的属性和信息
        - resource是一种资源的定义
    - terraform.tfstate 文件是一个 保存资源关系及其属性文件的数据库，如果损坏则需要重建所有的tf资源
    - Backend： 设置Backend可以将 .tfstate 文件推送至远端，所有人在使用时候都是同一个 .tfstate 文件
    - 
- 使用
  - terraform init [-h]
  - terraform plan
  - terraform apply
  - terraform destroy

- 代码案例
  - local provider install and test: https://developer.hashicorp.com/terraform/tutorials/providers/provider-setup
  - 由于不同provider提供的resource不一样，所以定义资源时要看provider对应的文档才行，官方也只是提供了terraform的基础语法以及简单应用
```text
# string, number, bool.
# list, set, map
# object, tuple
# any, null

# enter value: {a:"1",b:"2",c:3,d:null,f:["1"],h:[],j:[1,2],i:[],v:{},x:["18",12,true],z:{age:18,name:"simple"}} 
variable "an_object" {
  type = object({
    a = string
    b = string
    c = number
    d = any
    f = list(number)
    h = list(any) # 所有的value需要是统一类型
    j = set(string)
    i = set(any)
    v = map(number) # map的key必须是string
    z = object({ age = number, name = string })
    x = tuple([string, number, bool]) # = list(["18", "true", "john"])

    o = optional(string)
    t = optional(number, 216)
  })

  default = {
    a = "value"
    b = "value"
    c = 1
    d = null
    f = [1]
    h = []
    i = []
    j = ["value"]
    o = "value"
    t = 1
    v = {
      "key" = 1
    }
    x = ["value", 1, false]
    z = {
      age  = 1
      name = "value"
    }
  }
}

variable "image_id" {
  type        = string
  default     = "ami-xxxx"
  description = "an extra id" # 可以在输入变量中定义一个描述，简单地向调用者描述该变量的意义和用法

  validation {
    # 不符合条件则显示error message
    condition = can(regex("^ami-", var.image_id))
    # condition     = length(var.image_id) > 4 && substr(var.image_id,0,4)=="ami-"
    error_message = "The image_id value must be a valid AMI id, starting with \"ami-\"."
  }
}

variable "availability_zone_names" {
  type    = list(string)
  default = ["us-west-1a"]
}

variable "docker_ports" {
  type = list(object({
    internal = number
    external = number
    protocol = string
  }))

  default = [{
    external = 8300
    internal = 8888
    protocol = "tcp"
  }]
}

# {name:"zx",address:"123 12sa"}
variable "user_information" {
  type = object({
    name    = string
    address = string
  })

  default = {
    address = "xxxxx"
    name    = "xxxx"
  }
  sensitive = true
}

# resource "resource_name" "a" {

  # name    = var.user_information.name
  # address = var.user_information.address
  # nested_block {
  # At least one attribute in this block is (or was) sensitive,
  # so its contents will not be displayed.

  # }
# }

terraform {
  required_providers {
    hashicups = {
      version = "~> 0.3.1"
      source  = "hashicorp.com/edu/hashicups"
    }
  }
}

provider "hashicups" {
  username = "education"
  password = "test123"
}

# resource "hashicups_order" "edu" {
#   items {
#     coffee {
#       id = 3
#     }
#     quantity = 3
#   }
#   items {
#     coffee {
#       id = 2
#     }
#     quantity = 4
#   }
# }

# output "edu_order" {
#   value = hashicups_order.edu
# }
 
```