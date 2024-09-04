# File: getjwttoken.rb

class Getjwttoken < Formula
    desc "A tool to securely retrieve JWT tokens"
    homepage "https://github.com/jplonghi/homebrew-tools"
    url "https://github.com/jplonghi/homebrew-tools/archive/refs/tags/v1.0.0.tar.gz"
    version "1.0.0"
    sha256 "11224e5256b307fc67f3172bfbb6bbce59b051bf9a3ce172353e4fbb4b27c5eb"
  
    def install
      bin.install "getjwttoken"

      # Ensure the script is executable
      chmod "+x", bin/"getjwttoken"
    end
  end
  