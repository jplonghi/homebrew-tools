# File: getjwttoken.rb

class Getjwttoken < Formula
    desc "A tool to securely manage and retrieve JWT tokens"
    homepage "https://github.com/jplonghi/homebrew-tools"
    url "https://github.com/jplonghi/homebrew-tools/blob/main/getjwttoken"
    version "1.0.0"
    sha256 "4b5631f44444af515ff484ef5e93dbaf6beda7a6b9266adad217b4502ea21484"
  
    def install
      bin.install "getjwttoken"
    end
  
    test do
      system "#{bin}/getjwttoken", "--help"
    end
  end
  