# -*- mode: ruby -*-

# vi: set ft=ruby :

Vagrant.configure(2) do |config|

    config.vm.define "rtr" do |node|
      node.vm.box =  "IOS-XRv"
      node.vm.network :private_network, virtualbox__intnet: "link1", auto_config: false
    node.vm.provision "file", source: "configs/rtr_config1", destination: "/home/vagrant/rtr_config1"
    node.vm.provision "shell" do |s|
        s.path =  "scripts/apply_config.sh"
        s.args = ["/home/vagrant/rtr_config1"]
      end
    end


    config.vm.define "devbox" do |node|
      node.vm.box =  "ubuntu/trusty64"
      node.vm.network :private_network, virtualbox__intnet: "link1", ip: "11.1.1.20"
      node.vm.provision :shell, path: "scripts/bootstrap_devbox.sh", privileged: false
    end
end
