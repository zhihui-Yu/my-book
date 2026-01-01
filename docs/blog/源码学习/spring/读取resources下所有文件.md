# 读取resources下所有文件

---

## 使用spring的工具类
```java
try {
    PathMatchingResourcePatternResolver resolver = new PathMatchingResourcePatternResolver();
    Resource[] resources = resolver.getResources("classpath:static/**");
    for (var res : resources) {
        System.out.println("file => " + res.isFile() + ", name => " + res.getFilename() + ", read => " + res.isReadable());
        if (res instanceof FileSystemResource) {
            System.out.println("path1 => " + ((FileSystemResource) res).getPath());
        } else if (res instanceof ClassPathResource) {
            System.out.println("path2 => " + ((ClassPathResource) res).getPath());
        }
        System.out.println("URL => " + res.getURL());
        System.out.println("URI => " + res.getURI());
    }
} catch (Exception e) {
    System.out.println(e.getMessage());
}
```

PathMatchingResourcePatternResolver 内部如何获取文件的：
```java
protected Set<Resource> doFindPathMatchingJarResources(Resource rootDirResource, URL rootDirURL, String subPattern) {
....
    try {
        if (logger.isTraceEnabled()) {
            logger.trace("Looking for matching resources in jar file [" + jarFileUrl + "]");
        }
        if (StringUtils.hasLength(rootEntryPath) && !rootEntryPath.endsWith("/")) {
            // Root entry path must end with slash to allow for proper matching.
            // The Sun JRE does not return a slash here, but BEA JRockit does.
            rootEntryPath = rootEntryPath + "/";
        }
        Set<Resource> result = new LinkedHashSet<>(8);
        for (Enumeration<JarEntry> entries = jarFile.entries(); entries.hasMoreElements();) {
            JarEntry entry = entries.nextElement();
            String entryPath = entry.getName();
            if (entryPath.startsWith(rootEntryPath)) {
                String relativePath = entryPath.substring(rootEntryPath.length());
                if (getPathMatcher().match(subPattern, relativePath)) {
                    result.add(rootDirResource.createRelative(relativePath));
                }
            }
        }
        return result;
    } finally {
        if (closeJarFile) {
            jarFile.close();
        }
    }
}
```